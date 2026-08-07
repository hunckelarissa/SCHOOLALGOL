package org.myau.shaya.ide.debug.ui;

import org.eclipse.core.resources.IFile;
import org.eclipse.debug.core.model.IValue;
import org.eclipse.debug.ui.IDebugModelPresentation;
import org.eclipse.debug.ui.IValueDetailListener;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.part.FileEditorInput;
import org.myau.shaya.ide.debug.ShayaLineBreakpoint;
import org.myau.shaya.ide.debug.model.ShayaDebugTarget;
import org.myau.shaya.ide.debug.model.ShayaStackFrame;
import org.myau.shaya.ide.debug.model.ShayaThread;
import org.myau.shaya.ide.debug.model.ShayaVariable;

/**
 * Labels for Debug / Variables / Breakpoints views.
 */
public class ShayaDebugModelPresentation extends LabelProvider implements IDebugModelPresentation {

	@Override
	public void setAttribute(String attribute, Object value) {
		// no-op
	}

	@Override
	public String getText(Object element) {
		if (element instanceof ShayaDebugTarget) {
			return ((ShayaDebugTarget) element).getName();
		}
		if (element instanceof ShayaThread) {
			ShayaThread t = (ShayaThread) element;
			return t.isSuspended() ? "ALG (Suspended)" : "ALG";
		}
		if (element instanceof ShayaStackFrame) {
			return ((ShayaStackFrame) element).getName();
		}
		if (element instanceof ShayaVariable) {
			try {
				ShayaVariable v = (ShayaVariable) element;
				return v.getName() + " = " + v.getValue().getValueString();
			} catch (Exception e) {
				return ((ShayaVariable) element).getName();
			}
		}
		if (element instanceof ShayaLineBreakpoint) {
			try {
				ShayaLineBreakpoint bp = (ShayaLineBreakpoint) element;
				String res = bp.getMarker().getResource().getName();
				int line = bp.getLineNumber();
				StringBuilder extra = new StringBuilder();
				if (!bp.isEnabled()) {
					extra.append(" [disabled]");
				}
				if (bp.isConditionEnabled() && !bp.getCondition().isEmpty()) {
					extra.append(" [if ").append(bp.getCondition()).append("]");
				}
				int hit = bp.getHitCount();
				if (hit > 0) {
					extra.append(" [hit ").append(hit).append("]");
				}
				if (!bp.getLogMessage().isEmpty() && !bp.isSuspend()) {
					extra.append(" [log]");
				}
				return res + " [line: " + line + "]" + extra;
			} catch (Exception e) {
				return "ALG Breakpoint";
			}
		}
		return super.getText(element);
	}

	@Override
	public void computeDetail(IValue value, IValueDetailListener listener) {
		try {
			listener.detailComputed(value, value.getValueString());
		} catch (Exception e) {
			listener.detailComputed(value, "");
		}
	}

	@Override
	public IEditorInput getEditorInput(Object element) {
		if (element instanceof IFile) {
			return new FileEditorInput((IFile) element);
		}
		if (element instanceof ShayaStackFrame) {
			try {
				Object src = ((ShayaStackFrame) element).getAdapter(IFile.class);
				if (src instanceof IFile) {
					return new FileEditorInput((IFile) src);
				}
			} catch (Exception ignored) {
			}
		}
		return null;
	}

	@Override
	public String getEditorId(IEditorInput input, Object element) {
		return "org.myau.shaya.ide.editor.alg";
	}
}
