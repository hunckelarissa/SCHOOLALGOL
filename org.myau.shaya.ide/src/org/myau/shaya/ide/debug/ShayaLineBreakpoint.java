package org.myau.shaya.ide.debug;

import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.model.IBreakpoint;
import org.eclipse.debug.core.model.LineBreakpoint;
import org.myau.shaya.ide.debug.model.ShayaDebugElement;

/**
 * Строковая точка останова ALG — Breakpoints View
 * (enable / condition / hit count / log message / suspend).
 */
public class ShayaLineBreakpoint extends LineBreakpoint {

	public static final String MARKER_ID = "org.myau.shaya.ide.lineBreakpointMarker";
	public static final String ATTR_CONDITION = "org.myau.shaya.ide.condition";
	public static final String ATTR_CONDITION_ENABLED = "org.myau.shaya.ide.conditionEnabled";
	public static final String ATTR_HIT_COUNT = "org.myau.shaya.ide.hitCount";
	public static final String ATTR_LOG_MESSAGE = "org.myau.shaya.ide.logMessage";
	public static final String ATTR_SUSPEND = "org.myau.shaya.ide.suspend";

	/** Конструктор для восстановления из маркера (обязателен). */
	public ShayaLineBreakpoint() {
	}

	public ShayaLineBreakpoint(IResource resource, int lineNumber) throws CoreException {
		IMarker marker = resource.createMarker(MARKER_ID);
		setMarker(marker);
		setEnabled(true);
		ensureMarker().setAttribute(IBreakpoint.ID, getModelIdentifier());
		ensureMarker().setAttribute(IMarker.LINE_NUMBER, lineNumber);
		ensureMarker().setAttribute(IMarker.MESSAGE, "ALG: breakpoint at line " + lineNumber);
		ensureMarker().setAttribute(ATTR_CONDITION, "");
		ensureMarker().setAttribute(ATTR_CONDITION_ENABLED, Boolean.FALSE);
		ensureMarker().setAttribute(ATTR_HIT_COUNT, Integer.valueOf(0));
		ensureMarker().setAttribute(ATTR_LOG_MESSAGE, "");
		ensureMarker().setAttribute(ATTR_SUSPEND, Boolean.TRUE);
	}

	@Override
	public String getModelIdentifier() {
		return ShayaDebugElement.MODEL_ID;
	}

	public boolean supportsCondition() {
		return true;
	}

	public String getCondition() throws CoreException {
		String c = ensureMarker().getAttribute(ATTR_CONDITION, "");
		return c == null ? "" : c;
	}

	public void setCondition(String condition) throws CoreException {
		ensureMarker().setAttribute(ATTR_CONDITION, condition == null ? "" : condition);
	}

	public boolean isConditionEnabled() throws CoreException {
		return ensureMarker().getAttribute(ATTR_CONDITION_ENABLED, false);
	}

	public void setConditionEnabled(boolean enabled) throws CoreException {
		ensureMarker().setAttribute(ATTR_CONDITION_ENABLED, Boolean.valueOf(enabled));
	}

	public int getHitCount() throws CoreException {
		return ensureMarker().getAttribute(ATTR_HIT_COUNT, 0);
	}

	public void setHitCount(int hitCount) throws CoreException {
		ensureMarker().setAttribute(ATTR_HIT_COUNT, Integer.valueOf(Math.max(0, hitCount)));
	}

	public String getLogMessage() throws CoreException {
		String m = ensureMarker().getAttribute(ATTR_LOG_MESSAGE, "");
		return m == null ? "" : m;
	}

	public void setLogMessage(String message) throws CoreException {
		ensureMarker().setAttribute(ATTR_LOG_MESSAGE, message == null ? "" : message);
	}

	public boolean isSuspend() throws CoreException {
		return ensureMarker().getAttribute(ATTR_SUSPEND, true);
	}

	public void setSuspend(boolean suspend) throws CoreException {
		ensureMarker().setAttribute(ATTR_SUSPEND, Boolean.valueOf(suspend));
	}

	/** Условие для протокола (пусто если выключено). */
	public String effectiveCondition() throws CoreException {
		if (!isConditionEnabled()) {
			return "";
		}
		return getCondition().trim();
	}

	public static void create(IResource resource, int lineNumber) throws CoreException {
		ShayaLineBreakpoint bp = new ShayaLineBreakpoint(resource, lineNumber);
		DebugPlugin.getDefault().getBreakpointManager().addBreakpoint(bp);
	}
}
