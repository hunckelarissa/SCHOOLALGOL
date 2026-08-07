package org.myau.shaya.ide.debug;

import java.util.ArrayList;
import java.util.List;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.model.IBreakpoint;
import org.eclipse.debug.core.model.ILineBreakpoint;
import org.eclipse.jface.text.source.IVerticalRulerInfo;
import org.eclipse.swt.events.MouseAdapter;
import org.eclipse.swt.events.MouseEvent;
import org.eclipse.swt.widgets.Control;
import org.eclipse.ui.texteditor.ITextEditor;
import org.myau.shaya.ide.debug.model.ShayaDebugElement;

/**
 * Точки останова: BreakpointManager + Breakpoints View.
 * Совместимы с // @break в исходнике (оба способа).
 */
public final class ShayaBreakpoints {

	public static final class Spec {
		public final int line;
		public final boolean enabled;
		public final String condition;
		public final int hitCount;
		public final String logMessage;
		public final boolean suspend;
		/** Absolute OS path of the source file; empty = launch/main file. */
		public final String path;

		public Spec(int line, boolean enabled, String condition, int hitCount) {
			this(line, enabled, condition, hitCount, "", true, "");
		}

		public Spec(int line, boolean enabled, String condition, int hitCount,
				String logMessage, boolean suspend) {
			this(line, enabled, condition, hitCount, logMessage, suspend, "");
		}

		public Spec(int line, boolean enabled, String condition, int hitCount,
				String logMessage, boolean suspend, String path) {
			this.line = line;
			this.enabled = enabled;
			this.condition = condition == null ? "" : condition;
			this.hitCount = Math.max(0, hitCount);
			this.logMessage = logMessage == null ? "" : logMessage;
			this.suspend = suspend;
			this.path = path == null ? "" : path;
		}
	}

	private ShayaBreakpoints() {
	}

	public static void toggleAtRulerClick(ITextEditor editor, IVerticalRulerInfo rulerInfo, int y) {
		if (editor == null || rulerInfo == null) {
			return;
		}
		IFile file = fileFromEditor(editor);
		if (file == null) {
			return;
		}
		int line = rulerInfo.toDocumentLineNumber(y) + 1;
		if (line < 1) {
			return;
		}
		try {
			toggleLine(file, line);
		} catch (CoreException e) {
			// ignore
		}
	}

	public static void toggleLine(IResource resource, int line) throws CoreException {
		IBreakpoint existing = findBreakpoint(resource, line);
		if (existing != null) {
			DebugPlugin.getDefault().getBreakpointManager().removeBreakpoint(existing, true);
		} else {
			ShayaLineBreakpoint.create(resource, line);
		}
	}

	public static IBreakpoint findBreakpoint(IResource resource, int line) throws CoreException {
		IBreakpoint[] all = DebugPlugin.getDefault().getBreakpointManager()
				.getBreakpoints(ShayaDebugElement.MODEL_ID);
		for (IBreakpoint bp : all) {
			if (!(bp instanceof ILineBreakpoint)) {
				continue;
			}
			ILineBreakpoint lbp = (ILineBreakpoint) bp;
			if (resource.equals(lbp.getMarker().getResource()) && lbp.getLineNumber() == line) {
				return bp;
			}
		}
		return null;
	}

	/** Спеки для JSON-протокола (включая disabled). */
	public static List<Spec> collectSpecs(IFile file) {
		List<Spec> specs = new ArrayList<>();
		if (file == null || !file.exists()) {
			return specs;
		}
		String filePath = file.getLocation() != null ? file.getLocation().toOSString() : "";
		try {
			IBreakpoint[] all = DebugPlugin.getDefault().getBreakpointManager()
					.getBreakpoints(ShayaDebugElement.MODEL_ID);
			for (IBreakpoint bp : all) {
				if (!(bp instanceof ILineBreakpoint)) {
					continue;
				}
				ILineBreakpoint lbp = (ILineBreakpoint) bp;
				if (!file.equals(lbp.getMarker().getResource())) {
					continue;
				}
				int line = lbp.getLineNumber();
				boolean enabled = bp.isEnabled();
				String condition = "";
				int hit = 0;
				String logMessage = "";
				boolean suspend = true;
				if (bp instanceof ShayaLineBreakpoint) {
					ShayaLineBreakpoint sbp = (ShayaLineBreakpoint) bp;
					condition = sbp.effectiveCondition();
					hit = sbp.getHitCount();
					logMessage = sbp.getLogMessage();
					suspend = sbp.isSuspend();
				}
				specs.add(new Spec(line, enabled, condition, hit, logMessage, suspend, filePath));
			}
			for (org.eclipse.core.resources.IMarker m : file.findMarkers(
					"org.myau.shaya.ide.lineBreakpointMarker", true, IResource.DEPTH_ZERO)) {
				Object ln = m.getAttribute(org.eclipse.core.resources.IMarker.LINE_NUMBER);
				if (ln instanceof Integer) {
					int line = (Integer) ln;
					boolean present = false;
					for (Spec s : specs) {
						if (s.line == line) {
							present = true;
							break;
						}
					}
					if (!present) {
						specs.add(new Spec(line, true, "", 0, "", true, filePath));
					}
				}
			}
		} catch (CoreException e) {
			// ignore
		}
		return specs;
	}

	/**
	 * All ALG line breakpoints in the workspace (with absolute {@code path}).
	 * Needed for multi-file / include Step Debug.
	 */
	public static List<Spec> collectAllSpecs() {
		List<Spec> specs = new ArrayList<>();
		try {
			IBreakpoint[] all = DebugPlugin.getDefault().getBreakpointManager()
					.getBreakpoints(ShayaDebugElement.MODEL_ID);
			for (IBreakpoint bp : all) {
				if (!(bp instanceof ILineBreakpoint)) {
					continue;
				}
				ILineBreakpoint lbp = (ILineBreakpoint) bp;
				IResource res = lbp.getMarker().getResource();
				if (!(res instanceof IFile)) {
					continue;
				}
				IFile f = (IFile) res;
				String filePath = f.getLocation() != null ? f.getLocation().toOSString() : "";
				int line = lbp.getLineNumber();
				boolean enabled = bp.isEnabled();
				String condition = "";
				int hit = 0;
				String logMessage = "";
				boolean suspend = true;
				if (bp instanceof ShayaLineBreakpoint) {
					ShayaLineBreakpoint sbp = (ShayaLineBreakpoint) bp;
					condition = sbp.effectiveCondition();
					hit = sbp.getHitCount();
					logMessage = sbp.getLogMessage();
					suspend = sbp.isSuspend();
				}
				specs.add(new Spec(line, enabled, condition, hit, logMessage, suspend, filePath));
			}
		} catch (CoreException e) {
			// ignore
		}
		return specs;
	}

	/** Номера enabled-строк для --break (совместимость). */
	public static List<Integer> collectLines(IFile file) {
		List<Integer> lines = new ArrayList<>();
		for (Spec s : collectSpecs(file)) {
			if (s.enabled) {
				lines.add(s.line);
			}
		}
		return lines;
	}

	/** JSON-команда sync breakpoints (все ALG BP в workspace, с path). */
	public static String toProtocolCommand(IFile file) {
		List<Spec> specs = collectAllSpecs();
		if (specs.isEmpty() && file != null) {
			specs = collectSpecs(file);
		}
		StringBuilder sb = new StringBuilder();
		sb.append("{\"cmd\":\"breakpoints\",\"items\":[");
		for (int i = 0; i < specs.size(); i++) {
			Spec s = specs.get(i);
			if (i > 0) {
				sb.append(',');
			}
			sb.append("{\"line\":").append(s.line);
			sb.append(",\"enabled\":").append(s.enabled);
			sb.append(",\"hitCount\":").append(s.hitCount);
			sb.append(",\"condition\":\"").append(escapeJson(s.condition)).append("\"");
			sb.append(",\"logMessage\":\"").append(escapeJson(s.logMessage)).append("\"");
			sb.append(",\"suspend\":").append(s.suspend);
			if (s.path != null && !s.path.isBlank()) {
				sb.append(",\"path\":\"").append(escapeJson(s.path)).append("\"");
			}
			sb.append("}");
		}
		sb.append("]}");
		return sb.toString();
	}

	private static String escapeJson(String s) {
		return ShayaJson.escapeString(s);
	}

	public static void installRulerToggle(ITextEditor editor, Control rulerControl,
			IVerticalRulerInfo rulerInfo) {
		if (rulerControl == null || rulerInfo == null) {
			return;
		}
		rulerControl.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseDoubleClick(MouseEvent e) {
				toggleAtRulerClick(editor, rulerInfo, e.y);
			}
		});
	}

	private static IFile fileFromEditor(ITextEditor editor) {
		Object input = editor.getEditorInput();
		if (input instanceof org.eclipse.ui.IFileEditorInput) {
			return ((org.eclipse.ui.IFileEditorInput) input).getFile();
		}
		return null;
	}
}
