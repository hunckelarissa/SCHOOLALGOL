package org.myau.shaya.ide.debug;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Событие JSONL-протокола отладки (SHAYDBG …).
 */
public final class ShayaDebugEvent {

	public static final String PREFIX = "SHAYDBG ";

	public enum Kind {
		STOPPED, TERMINATED, EVAL, SET, UNKNOWN
	}

	/** Кадр стека (innermost-first после parse). */
	public static final class Frame {
		public final String name;
		public final Integer line;
		public final String source;
		public final String path;

		public Frame(String name, Integer line, String source) {
			this(name, line, source, "");
		}

		public Frame(String name, Integer line, String source, String path) {
			this.name = name == null || name.isEmpty() ? "main" : name;
			this.line = line;
			this.source = source == null ? "" : source;
			this.path = path == null ? "" : path;
		}

		public String label() {
			if (line != null && line.intValue() > 0) {
				return name + " [line " + line + "]";
			}
			return name;
		}
	}

	public final Kind kind;
	public final Integer line;
	public final String source;
	public final String reason;
	public final String path;
	public final Map<String, Object> globals;
	public final Map<String, Object> locals;
	public final Map<String, Object> arrays;
	public final Map<String, Object> records;
	public final List<String> stack;
	public final List<Frame> frames;
	public final String raw;
	public final String evalExpr;
	public final String evalValue;
	public final boolean evalOk;
	public final String evalError;
	public final String setName;
	public final String setValue;
	public final boolean setOk;
	public final String setError;

	private ShayaDebugEvent(Kind kind, Integer line, String source, String reason, String path,
			Map<String, Object> globals, Map<String, Object> locals,
			Map<String, Object> arrays, Map<String, Object> records,
			List<String> stack, List<Frame> frames,
			String raw, String evalExpr, String evalValue, boolean evalOk, String evalError,
			String setName, String setValue, boolean setOk, String setError) {
		this.kind = kind;
		this.line = line;
		this.source = source;
		this.reason = reason;
		this.path = path == null ? "" : path;
		this.globals = globals;
		this.locals = locals;
		this.arrays = arrays;
		this.records = records;
		this.stack = stack;
		this.frames = frames;
		this.raw = raw;
		this.evalExpr = evalExpr;
		this.evalValue = evalValue;
		this.evalOk = evalOk;
		this.evalError = evalError;
		this.setName = setName;
		this.setValue = setValue;
		this.setOk = setOk;
		this.setError = setError;
	}

	public static ShayaDebugEvent parseLine(String line) {
		if (line == null) {
			return null;
		}
		String t = line.trim();
		if (!t.startsWith(PREFIX)) {
			return null;
		}
		String json = t.substring(PREFIX.length()).trim();
		try {
			Map<String, Object> obj = ShayaJson.asObject(ShayaJson.parse(json));
			String shay = String.valueOf(obj.get("shay"));
			if ("terminated".equals(shay)) {
				return empty(Kind.TERMINATED, t);
			}
			if ("eval".equals(shay)) {
				String expr = obj.get("expr") == null ? "" : String.valueOf(obj.get("expr"));
				Object val = obj.get("value");
				boolean ok = !(obj.get("ok") instanceof Boolean) || Boolean.TRUE.equals(obj.get("ok"));
				String err = obj.get("error") == null ? "" : String.valueOf(obj.get("error"));
				return new ShayaDebugEvent(Kind.EVAL, null, null, null, "",
						Collections.emptyMap(), Collections.emptyMap(),
						Collections.emptyMap(), Collections.emptyMap(),
						Collections.emptyList(), Collections.emptyList(),
						t, expr, val == null ? "null" : String.valueOf(val), ok, err,
						null, null, false, null);
			}
			if ("set".equals(shay)) {
				String name = obj.get("name") == null ? "" : String.valueOf(obj.get("name"));
				Object val = obj.get("value");
				boolean ok = !(obj.get("ok") instanceof Boolean) || Boolean.TRUE.equals(obj.get("ok"));
				String err = obj.get("error") == null ? "" : String.valueOf(obj.get("error"));
				return new ShayaDebugEvent(Kind.SET, null, null, null, "",
						Collections.emptyMap(), Collections.emptyMap(),
						Collections.emptyMap(), Collections.emptyMap(),
						Collections.emptyList(), Collections.emptyList(),
						t, null, null, false, null,
						name, val == null ? "null" : stringify(val), ok, err);
			}
			if ("stopped".equals(shay)) {
				Integer lineNo = coerceLine(obj.get("line"));
				String source = obj.get("source") == null ? "" : String.valueOf(obj.get("source"));
				String reason = obj.get("reason") == null ? "" : String.valueOf(obj.get("reason"));
				String path = obj.get("path") == null ? "" : String.valueOf(obj.get("path"));
				Map<String, Object> globals = ShayaJson.asObject(obj.get("globals"));
				Map<String, Object> locals = ShayaJson.asObject(obj.get("locals"));
				Map<String, Object> arrays = ShayaJson.asObject(obj.get("arrays"));
				Map<String, Object> records = ShayaJson.asObject(obj.get("records"));
				List<Frame> frames = parseFrames(obj.get("stack"), lineNo, source, path);
				List<String> stack = new ArrayList<>();
				for (Frame f : frames) {
					stack.add(f.label());
				}
				if (stack.isEmpty()) {
					stack.add("main");
					frames = Collections.singletonList(new Frame("main", lineNo, source, path));
				}
				return new ShayaDebugEvent(Kind.STOPPED, lineNo, source, reason, path,
						globals, locals, arrays, records, stack, frames, t,
						null, null, false, null, null, null, false, null);
			}
			return empty(Kind.UNKNOWN, t);
		} catch (Exception e) {
			return empty(Kind.UNKNOWN, t);
		}
	}

	private static ShayaDebugEvent empty(Kind kind, String raw) {
		return new ShayaDebugEvent(kind, null, null, null, "",
				Collections.emptyMap(), Collections.emptyMap(),
				Collections.emptyMap(), Collections.emptyMap(),
				Collections.emptyList(), Collections.emptyList(),
				raw, null, null, false, null, null, null, false, null);
	}

	private static List<Frame> parseFrames(Object stackObj, Integer fallbackLine, String fallbackSource,
			String fallbackPath) {
		List<Frame> frames = new ArrayList<>();
		for (Object s : ShayaJson.asList(stackObj)) {
			if (s instanceof Map) {
				@SuppressWarnings("unchecked")
				Map<String, Object> m = (Map<String, Object>) s;
				String name = m.get("name") == null ? "main" : String.valueOf(m.get("name"));
				Integer ln = coerceLine(m.get("line"));
				String src = m.get("source") == null ? "" : String.valueOf(m.get("source"));
				String p = m.get("path") == null ? "" : String.valueOf(m.get("path"));
				if (p.isEmpty()) {
					p = fallbackPath;
				}
				frames.add(new Frame(name, ln, src, p));
			} else {
				frames.add(new Frame(String.valueOf(s), null, "", fallbackPath));
			}
		}
		if (frames.isEmpty()) {
			frames.add(new Frame("main", fallbackLine, fallbackSource, fallbackPath));
		} else if (frames.get(0).line == null && fallbackLine != null) {
			Frame top = frames.get(0);
			frames.set(0, new Frame(top.name, fallbackLine, fallbackSource,
					top.path.isEmpty() ? fallbackPath : top.path));
		}
		return frames;
	}

	private static Integer coerceLine(Object ln) {
		if (ln instanceof Number) {
			int n = ((Number) ln).intValue();
			return n > 0 ? Integer.valueOf(n) : null;
		}
		if (ln instanceof String) {
			String s = ((String) ln).trim();
			if (s.isEmpty() || "null".equalsIgnoreCase(s)) {
				return null;
			}
			try {
				int n = Integer.parseInt(s);
				return n > 0 ? Integer.valueOf(n) : null;
			} catch (NumberFormatException ignored) {
				return null;
			}
		}
		return null;
	}

	public static Map<String, String> flattenVars(Map<String, Object> map) {
		Map<String, String> out = new LinkedHashMap<>();
		if (map == null) {
			return out;
		}
		for (Map.Entry<String, Object> e : map.entrySet()) {
			out.put(e.getKey(), stringify(e.getValue()));
		}
		return out;
	}

	public static String stringify(Object v) {
		if (v == null) {
			return "null";
		}
		if (v instanceof String) {
			return "\"" + v + "\"";
		}
		if (v instanceof Map) {
			@SuppressWarnings("unchecked")
			Map<String, Object> m = (Map<String, Object>) v;
			Object kind = m.get("kind");
			if ("array".equals(String.valueOf(kind))) {
				Object size = m.get("size");
				Object trunc = m.get("truncated");
				String base = "массив[" + (size == null ? "?" : size) + "]";
				return Boolean.TRUE.equals(trunc) ? base + "…" : base;
			}
			if ("record".equals(String.valueOf(kind))) {
				Object fields = m.get("fields");
				int n = fields instanceof Map ? ((Map<?, ?>) fields).size() : 0;
				return "запись{" + n + "}";
			}
		}
		return String.valueOf(v);
	}
}
