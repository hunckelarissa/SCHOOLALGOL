package org.myau.shaya.ide.debug.model;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.eclipse.core.resources.IFile;
import org.eclipse.debug.core.DebugEvent;
import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.model.IBreakpoint;
import org.eclipse.debug.core.model.IStackFrame;
import org.eclipse.debug.core.model.IThread;
import org.eclipse.debug.core.model.IVariable;
import org.myau.shaya.ide.debug.ShayaDebugEvent;
import org.myau.shaya.ide.debug.ShayaLineBreakpoint;
import org.myau.shaya.ide.debug.ShayaSourceReveal;

/**
 * Единственный поток ALG-интерпретатора.
 */
public class ShayaThread extends ShayaDebugElement implements IThread {

	private final ShayaDebugTarget target;
	private ShayaStackFrame[] frames = new ShayaStackFrame[0];
	private Map<String, String> lastVarSnapshot;
	private boolean suspended;
	private boolean stepping;

	public ShayaThread(ShayaDebugTarget target) {
		super(target, target.getLaunch());
		this.target = target;
		this.frames = new ShayaStackFrame[] { new ShayaStackFrame(target, this, "main", null) };
	}

	void onStopped(ShayaDebugEvent event) {
		suspended = true;
		stepping = false;
		List<ShayaStackFrame> list = new ArrayList<>();
		List<ShayaDebugEvent.Frame> src = event.frames;
		if (src == null || src.isEmpty()) {
			list.add(new ShayaStackFrame(target, this, "main", event.line, event.source, event.path));
		} else {
			for (ShayaDebugEvent.Frame f : src) {
				Integer ln = f.line != null ? f.line : (list.isEmpty() ? event.line : null);
				String srcLine = f.source != null && !f.source.isEmpty() ? f.source
						: (list.isEmpty() ? event.source : "");
				String p = f.path != null && !f.path.isEmpty() ? f.path
						: (event.path == null ? "" : event.path);
				list.add(new ShayaStackFrame(target, this, f.name, ln, srcLine, p));
			}
		}
		frames = list.toArray(new ShayaStackFrame[0]);
		if (frames.length > 0) {
			frames[0].setPreviousValues(lastVarSnapshot);
			frames[0].updateVariables(event);
			lastVarSnapshot = frames[0].snapshotValues();
		}
		int detail = DebugEvent.BREAKPOINT;
		if (event.reason != null && event.reason.startsWith("step")) {
			detail = DebugEvent.STEP_END;
		}
		fireEvent(DebugEvent.SUSPEND, detail);
		if (frames.length > 0) {
			revealSource(frames[0]);
		}
	}

	void onSet(ShayaDebugEvent event) {
		if (!event.setOk || event.setName == null || event.setName.isEmpty()) {
			return;
		}
		String bare = event.setName;
		String text = event.setValue == null ? "null" : event.setValue;
		for (ShayaStackFrame frame : frames) {
			for (IVariable v : frame.getVariables()) {
				if (!(v instanceof ShayaVariable)) {
					continue;
				}
				ShayaVariable sv = (ShayaVariable) v;
				if (bare.equals(sv.bareName()) || ("local." + bare).equals(sv.getName())
						|| bare.equals(sv.getName())) {
					sv.applySetResult(text);
				}
			}
		}
		fireEvent(DebugEvent.CHANGE, DebugEvent.CONTENT);
	}

	void revealSource(final IStackFrame stackFrame) {
		if (!(stackFrame instanceof ShayaStackFrame)) {
			return;
		}
		ShayaStackFrame sf = (ShayaStackFrame) stackFrame;
		IFile fallback = ((ShayaDebugTarget) sf.getDebugTarget()).getProgramFile();
		ShayaSourceReveal.reveal(fallback, sf.getPath(), sf.getLineNumber());
	}

	void onResumed(int detail) {
		suspended = false;
		fireEvent(DebugEvent.RESUME, detail);
	}

	void onTerminated() {
		suspended = false;
		stepping = false;
		fireEvent(DebugEvent.TERMINATE, DebugEvent.CLIENT_REQUEST);
	}

	@Override
	public IStackFrame[] getStackFrames() {
		if (!isSuspended()) {
			return new IStackFrame[0];
		}
		return frames;
	}

	@Override
	public boolean hasStackFrames() {
		return isSuspended() && frames.length > 0;
	}

	@Override
	public int getPriority() {
		return 0;
	}

	@Override
	public IStackFrame getTopStackFrame() {
		return isSuspended() && frames.length > 0 ? frames[0] : null;
	}

	@Override
	public String getName() {
		return "ALG";
	}

	@Override
	public IBreakpoint[] getBreakpoints() {
		if (!isSuspended() || frames.length == 0) {
			return new IBreakpoint[0];
		}
		ShayaStackFrame top = frames[0];
		int line = top.getLineNumber();
		if (line <= 0) {
			return new IBreakpoint[0];
		}
		String framePath = top.getPath() == null ? "" : top.getPath();
		List<IBreakpoint> hits = new ArrayList<>();
		try {
			IBreakpoint[] all = DebugPlugin.getDefault().getBreakpointManager()
					.getBreakpoints(ShayaDebugElement.MODEL_ID);
			for (IBreakpoint bp : all) {
				if (!(bp instanceof ShayaLineBreakpoint) || !bp.isEnabled()) {
					continue;
				}
				ShayaLineBreakpoint sbp = (ShayaLineBreakpoint) bp;
				if (sbp.getLineNumber() != line) {
					continue;
				}
				if (!framePath.isEmpty() && sbp.getMarker() != null
						&& sbp.getMarker().getResource() != null
						&& sbp.getMarker().getResource().getLocation() != null) {
					String bpPath = sbp.getMarker().getResource().getLocation().toOSString();
					String a = bpPath.replace('\\', '/');
					String b = framePath.replace('\\', '/');
					if (!a.equalsIgnoreCase(b) && !b.endsWith("/" + sbp.getMarker().getResource().getName())
							&& !a.endsWith(b) && !b.endsWith(a)) {
						// Path mismatch: still accept if basename matches (multi-file)
						String bn = sbp.getMarker().getResource().getName();
						if (!b.toLowerCase().endsWith("/" + bn.toLowerCase())
								&& !b.equalsIgnoreCase(bn)) {
							continue;
						}
					}
				}
				hits.add(bp);
			}
		} catch (Exception ignored) {
		}
		return hits.toArray(new IBreakpoint[0]);
	}

	@Override
	public boolean canResume() {
		return !isTerminated() && isSuspended();
	}

	@Override
	public boolean canSuspend() {
		return false;
	}

	@Override
	public boolean isSuspended() {
		return suspended && !isTerminated();
	}

	@Override
	public void resume() throws DebugException {
		target.cont();
		stepping = false;
		onResumed(DebugEvent.CLIENT_REQUEST);
	}

	@Override
	public void suspend() throws DebugException {
		notSupported("suspend");
	}

	@Override
	public boolean canStepInto() {
		return canResume();
	}

	@Override
	public boolean canStepOver() {
		return canResume();
	}

	@Override
	public boolean canStepReturn() {
		return canResume() && frames.length > 1;
	}

	@Override
	public boolean isStepping() {
		return stepping;
	}

	@Override
	public void stepInto() throws DebugException {
		target.stepInto();
		stepping = true;
		onResumed(DebugEvent.STEP_INTO);
	}

	@Override
	public void stepOver() throws DebugException {
		target.step();
		stepping = true;
		onResumed(DebugEvent.STEP_OVER);
	}

	@Override
	public void stepReturn() throws DebugException {
		target.stepOut();
		stepping = true;
		onResumed(DebugEvent.STEP_RETURN);
	}

	@Override
	public boolean canTerminate() {
		return !isTerminated();
	}

	@Override
	public boolean isTerminated() {
		return target.isTerminated();
	}

	@Override
	public void terminate() throws DebugException {
		target.terminate();
	}
}
