package org.myau.shaya.ide.debug;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Минимальный JSON-парсер (без сторонних библиотек) для debug-протокола ALG.
 */
public final class ShayaJson {

	private ShayaJson() {
	}

	public static Object parse(String text) {
		Parser p = new Parser(text);
		Object v = p.parseValue();
		p.skipWs();
		return v;
	}

	/**
	 * Экранирование строки для JSON (симметрично {@link #parse} / parseString).
	 * Обрабатывает backslash, quote и control-символы (b/f/n/r/t и прочие как unicode escapes).
	 */
	public static String escapeString(String s) {
		if (s == null || s.isEmpty()) {
			return "";
		}
		StringBuilder sb = new StringBuilder(s.length() + 8);
		for (int i = 0; i < s.length(); i++) {
			char c = s.charAt(i);
			switch (c) {
			case '"':
				sb.append("\\\"");
				break;
			case '\\':
				sb.append("\\\\");
				break;
			case '\b':
				sb.append("\\b");
				break;
			case '\f':
				sb.append("\\f");
				break;
			case '\n':
				sb.append("\\n");
				break;
			case '\r':
				sb.append("\\r");
				break;
			case '\t':
				sb.append("\\t");
				break;
			default:
				if (c < 0x20) {
					sb.append(String.format("\\u%04x", (int) c));
				} else {
					sb.append(c);
				}
			}
		}
		return sb.toString();
	}

	@SuppressWarnings("unchecked")
	public static Map<String, Object> asObject(Object o) {
		if (o instanceof Map) {
			return (Map<String, Object>) o;
		}
		return Collections.emptyMap();
	}

	@SuppressWarnings("unchecked")
	public static List<Object> asList(Object o) {
		if (o instanceof List) {
			return (List<Object>) o;
		}
		return Collections.emptyList();
	}

	private static final class Parser {
		private final String s;
		private int i;

		Parser(String s) {
			this.s = s == null ? "" : s;
		}

		void skipWs() {
			while (i < s.length() && Character.isWhitespace(s.charAt(i))) {
				i++;
			}
		}

		Object parseValue() {
			skipWs();
			if (i >= s.length()) {
				return null;
			}
			char c = s.charAt(i);
			if (c == '{') {
				return parseObject();
			}
			if (c == '[') {
				return parseArray();
			}
			if (c == '"') {
				return parseString();
			}
			if (c == 't' || c == 'f') {
				return parseBool();
			}
			if (c == 'n') {
				return parseNull();
			}
			return parseNumber();
		}

		Map<String, Object> parseObject() {
			Map<String, Object> map = new LinkedHashMap<>();
			i++; // {
			skipWs();
			if (i < s.length() && s.charAt(i) == '}') {
				i++;
				return map;
			}
			while (i < s.length()) {
				skipWs();
				String key = parseString();
				skipWs();
				expect(':');
				Object val = parseValue();
				map.put(key, val);
				skipWs();
				if (i < s.length() && s.charAt(i) == ',') {
					i++;
					continue;
				}
				expect('}');
				break;
			}
			return map;
		}

		List<Object> parseArray() {
			List<Object> list = new ArrayList<>();
			i++; // [
			skipWs();
			if (i < s.length() && s.charAt(i) == ']') {
				i++;
				return list;
			}
			while (i < s.length()) {
				list.add(parseValue());
				skipWs();
				if (i < s.length() && s.charAt(i) == ',') {
					i++;
					continue;
				}
				expect(']');
				break;
			}
			return list;
		}

		String parseString() {
			expect('"');
			StringBuilder sb = new StringBuilder();
			while (i < s.length()) {
				char c = s.charAt(i++);
				if (c == '"') {
					return sb.toString();
				}
				if (c == '\\' && i < s.length()) {
					char e = s.charAt(i++);
					switch (e) {
					case '"':
					case '\\':
					case '/':
						sb.append(e);
						break;
					case 'b':
						sb.append('\b');
						break;
					case 'f':
						sb.append('\f');
						break;
					case 'n':
						sb.append('\n');
						break;
					case 'r':
						sb.append('\r');
						break;
					case 't':
						sb.append('\t');
						break;
					case 'u':
						if (i + 4 <= s.length()) {
							int code = Integer.parseInt(s.substring(i, i + 4), 16);
							sb.append((char) code);
							i += 4;
						}
						break;
					default:
						sb.append(e);
					}
				} else {
					sb.append(c);
				}
			}
			return sb.toString();
		}

		Boolean parseBool() {
			if (s.startsWith("true", i)) {
				i += 4;
				return Boolean.TRUE;
			}
			if (s.startsWith("false", i)) {
				i += 5;
				return Boolean.FALSE;
			}
			throw new IllegalArgumentException("bool at " + i);
		}

		Object parseNull() {
			if (s.startsWith("null", i)) {
				i += 4;
				return null;
			}
			throw new IllegalArgumentException("null at " + i);
		}

		Number parseNumber() {
			int start = i;
			if (i < s.length() && (s.charAt(i) == '-' || s.charAt(i) == '+')) {
				i++;
			}
			while (i < s.length() && Character.isDigit(s.charAt(i))) {
				i++;
			}
			boolean real = false;
			if (i < s.length() && s.charAt(i) == '.') {
				real = true;
				i++;
				while (i < s.length() && Character.isDigit(s.charAt(i))) {
					i++;
				}
			}
			String num = s.substring(start, i);
			if (real) {
				return Double.valueOf(num);
			}
			try {
				return Integer.valueOf(num);
			} catch (NumberFormatException e) {
				return Long.valueOf(num);
			}
		}

		void expect(char c) {
			skipWs();
			if (i >= s.length() || s.charAt(i) != c) {
				throw new IllegalArgumentException("expected " + c + " at " + i);
			}
			i++;
		}
	}
}
