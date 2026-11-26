import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public final class Frame {
    private static long word(String input) {
        if (!input.matches("[0-9]{1,10}")) {
            throw new IllegalArgumentException("esperado uint32 decimal");
        }
        long value = Long.parseLong(input);
        if (value > 0xffffffffL) {
            throw new IllegalArgumentException("valor acima de uint32");
        }
        return value;
    }

    public static void main(String[] args) throws IOException {
        try {
            if (args.length != 4) {
                throw new IllegalArgumentException("uso: Frame admission|recovery A B C");
            }
            int operation = switch (args[0]) {
                case "admission" -> 1;
                case "recovery" -> 2;
                default -> throw new IllegalArgumentException("operação desconhecida");
            };
            var buffer = ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN);
            buffer.putInt(operation);
            for (int index = 1; index < args.length; index++) {
                buffer.putInt((int) word(args[index]));
            }
            System.out.write(buffer.array());
            System.out.flush();
            if (System.out.checkError()) {
                throw new IOException("falha ao gravar o quadro");
            }
        } catch (IllegalArgumentException error) {
            System.err.println(error.getMessage());
            System.exit(64);
        }
    }
}
