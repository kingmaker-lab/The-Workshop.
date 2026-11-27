// Ruby Orion Studio worker. Ruby runs in the browser, not on the Cloudflare server.
// Version-pinned ruby.wasm runtime; user code never enters a JavaScript template unescaped.
import { DefaultRubyVM } from "https://cdn.jsdelivr.net/npm/@ruby/wasm-wasi@2.10.1/dist/browser/+esm";

const WASM_URL = "https://cdn.jsdelivr.net/npm/@ruby/3.4-wasm-wasi@2.10.1/dist/ruby+stdlib.wasm";
const MAX_CODE = 8000;
const MAX_INPUT = 4000;
let modulePromise;
let busy = false;

function toBase64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 4096) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 4096));
  }
  return btoa(binary);
}

async function getCompiledModule() {
  if (!modulePromise) {
    modulePromise = (async () => {
      self.postMessage({ type: "booting", message: "Carregando CRuby 3.4 via WebAssembly..." });
      const response = await fetch(WASM_URL, { credentials: "omit", redirect: "error" });
      if (!response.ok) throw new Error("Falha ao carregar Ruby/WASM (HTTP " + response.status + ").");
      const bytes = await response.arrayBuffer();
      return WebAssembly.compile(bytes);
    })();
  }
  return modulePromise;
}

function rubyProgram(source, stdin) {
  const encodedSource = toBase64(source);
  const encodedInput = toBase64(stdin);
  // Only generated Base64 strings are interpolated into the Ruby wrapper.
  return [
    "require 'base64'",
    "require 'json'",
    "require 'stringio'",
    "__orion_src__ = Base64.strict_decode64('" + encodedSource + "')",
    "__orion_input__ = Base64.strict_decode64('" + encodedInput + "')",
    "__orion_limiter__ = Class.new do",
    "  LIMIT = 12_000",
    "  attr_reader :truncated",
    "  def initialize; @parts = []; @count = 0; @truncated = false; end",
    "  def write(obj)",
    "    text = obj.to_s",
    "    bytes = text.b",
    "    remaining = LIMIT - @count",
    "    accepted = bytes.byteslice(0, [remaining, 0].max)",
    "    if accepted && !accepted.empty?; @parts << accepted; @count += accepted.bytesize; end",
    "    @truncated = true if bytes.bytesize > [remaining, 0].max",
    "    bytes.bytesize",
    "  end",
    "  def puts(*args)",
    "    args = [nil] if args.empty?",
    "    args.each do |arg|",
    "      s = arg.nil? ? '' : arg.to_s",
    "      write(s.end_with?(\"\\n\") ? s : s + \"\\n\")",
    "    end",
    "    nil",
    "  end",
    "  def print(*args); args.each { |arg| write(arg.to_s) }; nil; end",
    "  def <<(value); write(value); self; end",
    "  def flush; self; end",
    "  def tty?; false; end",
    "  def sync=(value); end",
    "  def string; @parts.join.force_encoding('UTF-8').scrub; end",
    "end",
    "__orion_stdout__ = __orion_limiter__.new",
    "__orion_stderr__ = __orion_limiter__.new",
    "__orion_previous_stdin__ = $stdin",
    "__orion_previous_stdout__ = $stdout",
    "__orion_previous_stderr__ = $stderr",
    "$stdin = StringIO.new(__orion_input__)",
    "$stdout = __orion_stdout__",
    "$stderr = __orion_stderr__",
    "begin",
    "  TOPLEVEL_BINDING.eval(__orion_src__, 'orion_studio.rb', 1)",
    "rescue Exception => e",
    "  __orion_stderr__.puts \"#{e.class}: #{e.message}\"",
    "ensure",
    "  $stdin = __orion_previous_stdin__",
    "  $stdout = __orion_previous_stdout__",
    "  $stderr = __orion_previous_stderr__",
    "end",
    "JSON.generate({ output: __orion_stdout__.string, error: __orion_stderr__.string, truncated: (__orion_stdout__.truncated || __orion_stderr__.truncated) })"
  ].join("\n");
}

async function evaluate(source, stdin, id) {
  const compiled = await getCompiledModule();
  const { vm } = await DefaultRubyVM(compiled);
  self.postMessage({ type: "running", id });
  const result = vm.eval(rubyProgram(source, stdin));
  const output = JSON.parse(result.toString());
  return {
    output: String(output.output || "").slice(0, 12000),
    error: String(output.error || "").slice(0, 12000),
    truncated: output.truncated === true
  };
}

self.onmessage = async event => {
  const message = event.data;
  if (!message || busy) return;
  const { id, code, input } = message;
  if (!Number.isInteger(id) || typeof code !== "string") return;
  if (message.type !== "run" && message.type !== "suite") return;
  if (code.length > MAX_CODE) {
    self.postMessage({ type: "fatal", id, message: "Limite de código excedido (8.000 caracteres)." });
    return;
  }
  const suite = message.type === "suite";
  const cases = suite ? message.cases : [{ input }];
  if (!Array.isArray(cases) || cases.length < 1 || cases.length > 6 ||
      cases.some(test => !test || typeof test.input !== "string" || test.input.length > MAX_INPUT)) {
    self.postMessage({ type: "fatal", id, message: "Suíte inválida: máximo de 6 casos e 4.000 caracteres de entrada por caso." });
    return;
  }
  busy = true;
  try {
    if (!suite) {
      const result = await evaluate(code, input, id);
      self.postMessage({ type: "result", id, ...result });
    } else {
      await getCompiledModule();
      self.postMessage({ type: "suite-ready", id, count: cases.length });
      for (let index = 0; index < cases.length; index++) {
        const before = performance.now();
        const result = await evaluate(code, cases[index].input, id);
        self.postMessage({
          type: "suite-case", id, index,
          durationMs: Math.round(performance.now() - before),
          ...result
        });
      }
      self.postMessage({ type: "suite-done", id, count: cases.length });
    }
  } catch (error) {
    self.postMessage({ type: "fatal", id, message: String(error && error.message || error).slice(0, 600) });
  } finally {
    busy = false;
  }
};
