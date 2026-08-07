package org.myau.shaya.ide.markers;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;

/**
 * Parses interpreter stdout/stderr into Eclipse problem markers.
 * Interpreters are Python scripts; diagnostics are typically "file:line: message"
 * or "line N: message" / "строка N: message" style — patterns are dialect-agnostic
 * on purpose (engines are not obligated to share an error format).
 */
public final class ShayaMarkers {

	/** Dedicated marker so Problems view can filter "ALG". */
	public static final String MARKER_TYPE = "org.myau.shaya.ide.shayaProblem";

	/**
	 * path:line:col: message — Windows drive paths need the {@code C:\} prefix
	 * consumed before the line/column colon (otherwise {@code C} alone matches).
	 */
	private static final Pattern P_FILE_LINE_COL = Pattern.compile(
			"^\"?((?:[A-Za-z]:[\\\\/])?[^\":]+?)\"?\\s*:\\s*(\\d+)\\s*:\\s*(\\d+)\\s*:?\\s*(.*)$");

	/** path:line: message (same Windows-drive handling). */
	private static final Pattern P_FILE_LINE = Pattern.compile(
			"^\"?((?:[A-Za-z]:[\\\\/])?[^\":]+?)\"?\\s*:\\s*(\\d+)\\s*:\\s*(.*)$");

	/** line N: msg / строка N: msg */
	private static final Pattern P_LINE_WORD = Pattern.compile(
			"(?i)(?:line|строка)\\s*(\\d+)\\s*[:.]\\s*(.*)$");

	/** Python traceback tail: File "x.py", line N, in ... — noise, not a ALG source error */
	private static final Pattern P_PY_TRACEBACK = Pattern.compile(
			"^\\s*File \"[^\"]+\\.py\"");

	private ShayaMarkers() {
	}

	public static void clear(IFile file) throws CoreException {
		file.deleteMarkers(MARKER_TYPE, true, IResource.DEPTH_ZERO);
	}

	public static void applyFromProcessOutput(IFile file, String output, int exitCode) throws CoreException {
		clear(file);
		String baseName = file.getName().toLowerCase(Locale.ROOT);
		if (output == null || output.isBlank()) {
			if (exitCode != 0) {
				create(file, 1, 0, failMessage(baseName, output, exitCode), IMarker.SEVERITY_ERROR);
			}
			return;
		}
		boolean any = false;
		for (String line : output.split("\\R")) {
			String trimmed = line.trim();
			if (trimmed.isEmpty() || trimmed.startsWith("[ALG]") || trimmed.startsWith("[SHAYA]")
					|| trimmed.startsWith(">>>")
					|| P_PY_TRACEBACK.matcher(trimmed).find()) {
				continue;
			}
			Parsed p = parseStructured(trimmed, baseName);
			if (p == null) {
				continue;
			}
			create(file, p.line, p.column, p.message, p.severity);
			any = true;
		}
		if (!any && exitCode != 0) {
			for (String line : output.split("\\R")) {
				String trimmed = line.trim();
				if (trimmed.isEmpty() || trimmed.startsWith("[ALG]") || trimmed.startsWith("[SHAYA]")
						|| !isErrorish(trimmed)) {
					continue;
				}
				create(file, 1, 0, trimmed, severity(trimmed));
				any = true;
				break;
			}
			if (!any) {
				create(file, 1, 0, failMessage(baseName, output, exitCode), IMarker.SEVERITY_ERROR);
			}
		}
	}

	private static String failMessage(String baseName, String output, int exitCode) {
		return "Run failed (exit " + exitCode + "). See ALG console.";
	}

	/** Structured diagnostics only (path:line / строка N) — not loose “errorish” text. */
	static Parsed parseStructured(String trimmed, String baseName) {
		Matcher m = P_FILE_LINE_COL.matcher(trimmed);
		if (m.find()) {
			String path = m.group(1);
			int line = atoi(m.group(2));
			int col = atoi(m.group(3));
			if (pathRelevant(path, baseName)) {
				return new Parsed(Math.max(1, line), col, m.group(4), severity(trimmed));
			}
		}
		m = P_FILE_LINE.matcher(trimmed);
		if (m.find()) {
			String path = m.group(1);
			int line = atoi(m.group(2));
			if (pathRelevant(path, baseName) && !path.matches("(?i)exit|cwd|toolchain|python")) {
				return new Parsed(Math.max(1, line), 0, m.group(3), severity(trimmed));
			}
		}
		m = P_LINE_WORD.matcher(trimmed);
		if (m.find()) {
			return new Parsed(atoi(m.group(1)), 0, m.group(2), severity(trimmed));
		}
		return null;
	}

	/** Compatibility wrapper: structured first, then loose errorish (tests / older callers). */
	@Deprecated
	static Parsed parse(String trimmed, String baseName) {
		Parsed p = parseStructured(trimmed, baseName);
		if (p != null) {
			return p;
		}
		if (isErrorish(trimmed)) {
			return new Parsed(1, 0, trimmed, severity(trimmed));
		}
		return null;
	}

	private static boolean isErrorish(String line) {
		String l = line.toLowerCase(Locale.ROOT);
		return l.contains("error") || l.contains("ошибка") || l.contains("traceback")
				|| l.contains("exception");
	}

	private static boolean pathRelevant(String path, String baseName) {
		if (path == null || path.isBlank() || "(null)".equals(path)) {
			return true;
		}
		String n = path.replace('\\', '/').replace("\"", "").trim();
		int slash = n.lastIndexOf('/');
		String leaf = slash >= 0 ? n.substring(slash + 1) : n;
		String leafLower = leaf.toLowerCase(Locale.ROOT);
		if (leafLower.equals(baseName)) {
			return true;
		}
		String stem = baseName.replaceAll("\\.[^.]+$", "");
		return leafLower.startsWith(stem);
	}

	private static int severity(String line) {
		String l = line.toLowerCase(Locale.ROOT);
		if (l.contains("hint") || l.contains("подсказ")) {
			return IMarker.SEVERITY_INFO;
		}
		if (l.contains("warning") || l.contains("предупрежд")) {
			return IMarker.SEVERITY_WARNING;
		}
		return IMarker.SEVERITY_ERROR;
	}

	/** Short tip for common interpreter messages (Problems view). */
	static String tipFor(String fileName, String message) {
		if (message == null) {
			return null;
		}
		String m = message.toLowerCase(Locale.ROOT);
		String n = fileName == null ? "" : fileName.toLowerCase(Locale.ROOT);
		if (n.endsWith(".alg")) {
			if (m.contains("алг") || m.contains("ожида") || m.contains("syntax")
					|| m.contains("синтакс") || m.contains("нач") || m.contains("кон")) {
				return "Проверьте алг / нач / кон (классический Кушниренко .alg)";
			}
		}
		if (m.contains("python") && (m.contains("not found") || m.contains("не найден"))) {
			return "Install Python 3 and put it on PATH (py -3 / python)";
		}
		if (m.contains("unknown shaya extension")) {
			return "Поддерживается только .alg → SCHOOLALGOL";
		}
		return null;
	}

	private static int atoi(String s) {
		try {
			return Integer.parseInt(s);
		} catch (Exception e) {
			return 1;
		}
	}

	private static void create(IFile file, int line, int column, String message, int severity)
			throws CoreException {
		IMarker marker = file.createMarker(MARKER_TYPE);
		String base = message == null || message.isBlank() ? "error" : message.trim();
		String tip = tipFor(file.getName(), base);
		marker.setAttribute(IMarker.MESSAGE, tip == null ? base : base + " — tip: " + tip);
		marker.setAttribute(IMarker.SEVERITY, severity);
		int safeLine = Math.max(1, line);
		marker.setAttribute(IMarker.LINE_NUMBER, safeLine);
		if (column > 0) {
			marker.setAttribute(IMarker.LOCATION, "line " + safeLine + " col " + column);
			int[] range = charRange(file, safeLine, column);
			if (range != null) {
				marker.setAttribute(IMarker.CHAR_START, Integer.valueOf(range[0]));
				marker.setAttribute(IMarker.CHAR_END, Integer.valueOf(range[1]));
			}
		}
	}

	/**
	 * Map 1-based line/col to document offsets for Problems jump-to-column.
	 *
	 * @return {start,end} or null
	 */
	private static int[] charRange(IFile file, int line, int column) {
		try (InputStream in = file.getContents(true)) {
			byte[] bytes = in.readAllBytes();
			String text = new String(bytes, StandardCharsets.UTF_8);
			int curLine = 1;
			int offset = 0;
			int lineStart = 0;
			while (offset < text.length() && curLine < line) {
				char c = text.charAt(offset++);
				if (c == '\r') {
					if (offset < text.length() && text.charAt(offset) == '\n') {
						offset++;
					}
					curLine++;
					lineStart = offset;
				} else if (c == '\n') {
					curLine++;
					lineStart = offset;
				}
			}
			if (curLine != line) {
				return null;
			}
			int lineEnd = lineStart;
			while (lineEnd < text.length()) {
				char c = text.charAt(lineEnd);
				if (c == '\n' || c == '\r') {
					break;
				}
				lineEnd++;
			}
			int col0 = Math.max(0, column - 1);
			if (lineStart >= lineEnd) {
				return null;
			}
			int start = Math.min(lineStart + col0, lineEnd - 1);
			int end = Math.min(start + 1, lineEnd);
			if (end <= start) {
				return null;
			}
			return new int[] { start, end };
		} catch (Exception e) {
			return null;
		}
	}

	static final class Parsed {
		final int line;
		final int column;
		final String message;
		final int severity;

		Parsed(int line, int column, String message, int severity) {
			this.line = line;
			this.column = column;
			this.message = message;
			this.severity = severity;
		}
	}
}
