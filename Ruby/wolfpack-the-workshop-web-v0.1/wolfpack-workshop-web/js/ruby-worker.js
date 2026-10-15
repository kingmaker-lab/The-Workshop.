// ruby.wasm roda dentro de um Web Worker para não bloquear a interface.
// Não é um sandbox de segurança para código de terceiros. Não exponha dados sensíveis no origin.
// Versões fixadas, evitando dependência de "latest".
import { DefaultRubyVM } from 'https://cdn.jsdelivr.net/npm/@ruby/wasm-wasi@2.10.1/dist/browser/+esm';

const WASM_URL = 'https://cdn.jsdelivr.net/npm/@ruby/3.3-wasm-wasi@2.10.1/dist/ruby+stdlib.wasm';
let compiledModule;

function b64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  for (let i = 0; i < bytes.length; i += 16384) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 16384));
  }
  return btoa(binary);
}

async function getModule() {
  if (!compiledModule) {
    self.postMessage({ type: 'status', message: 'Carregando o interpretador Ruby 3.3 (primeira execução)...' });
    const response = await fetch(WASM_URL);
    if (!response.ok) throw new Error(`Não foi possível carregar o interpretador: HTTP ${response.status}`);
    const buffer = await response.arrayBuffer();
    compiledModule = await WebAssembly.compile(buffer);
  }
  return compiledModule;
}

function norm(text) {
  return String(text).replace(/\r\n/g, '\n').replace(/\n$/, '');
}

async function runCase(module, source, input) {
  const { vm } = await DefaultRubyVM(module);
  const encodedSource = b64(source);
  const encodedInput = b64(input);
  // Transferência Base64: nunca concatenar código do jogador diretamente na expressão hospedeira.
  // StringIO substitui a entrada e a saída globais durante a avaliação.
  const script = `
require 'base64'
require 'stringio'
require 'json'
__wp_source__ = Base64.strict_decode64('${encodedSource}')
__wp_stdin__ = Base64.strict_decode64('${encodedInput}')
__wp_output__ = StringIO.new
__wp_error__ = StringIO.new
$stdin = StringIO.new(__wp_stdin__)
$stdout = __wp_output__
$stderr = __wp_error__
begin
  TOPLEVEL_BINDING.eval(__wp_source__, 'wolfpack_mission.rb', 1)
rescue Exception => e
  __wp_error__.puts "#{e.class}: #{e.message}"
end
$stdout = STDOUT
$stderr = STDERR
JSON.generate({output: __wp_output__.string, error: __wp_error__.string})
`;
  const result = vm.eval(script);
  const data = JSON.parse(result.toString());
  const maxSize = 16000;
  return {
    output: data.output.length > maxSize ? data.output.slice(0, maxSize) : data.output,
    error: data.error.length > maxSize ? data.error.slice(0, maxSize) : data.error,
    exceeded: data.output.length > maxSize || data.error.length > maxSize
  };
}

self.onmessage = async event => {
  if (event.data?.type !== 'run') return;
  const { code, cases } = event.data;
  try {
    if (typeof code !== 'string' || code.length > 12000) throw new Error('Código muito longo (máximo 12.000 caracteres).');
    const module = await getModule();
    for (let index = 0; index < cases.length; index++) {
      self.postMessage({ type: 'case-start', index });
      const result = await runCase(module, code, cases[index].input);
      if (result.error) {
        self.postMessage({ type: 'result', success: false, index, reason: 'O Ruby encontrou um erro:', actual: result.error });
        return;
      }
      if (result.exceeded) {
        self.postMessage({ type: 'result', success: false, index, reason: 'Saída excedeu o limite de 16 mil caracteres.', actual: result.output });
        return;
      }
      if (norm(result.output) !== norm(cases[index].output)) {
        self.postMessage({ type: 'result', success: false, index, reason: 'A saída do programa ainda não corresponde ao desafio.', actual: result.output, expected: cases[index].output });
        return;
      }
    }
    self.postMessage({ type: 'result', success: true, count: cases.length });
  } catch (error) {
    self.postMessage({ type: 'fatal', message: String(error?.message || error) });
  }
};
