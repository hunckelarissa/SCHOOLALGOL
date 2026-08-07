package org.myau.shaya.ide.debug.model;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IResource;
import org.eclipse.debug.core.DebugEvent;
import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.ILaunch;
import org.eclipse.debug.core.model.IBreakpoint;
import org.eclipse.debug.core.model.IDebugTarget;
import org.eclipse.debug.core.model.IMemoryBlock;
import org.eclipse.debug.core.model.IProcess;
import org.eclipse.debug.core.model.IStreamsProxy;
import org.eclipse.debug.core.model.IThread;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.debug.ShayaBreakpoints;
import org.myau.shaya.ide.debug.ShayaDebugEvent;
import org.myau.shaya.ide.debug.ShayaJson;
import org.myau.shaya.ide.debug.ShayaSourceReveal;

/**
 * {@link IDebugTarget} over one wire protocol: {@code --debug-protocol} / {@code SHAYDBG} JSONL.
 * CLI Debug ({@code --debug}) stays a separate console path and is not handled here.
 */
public class ShayaDebugTarget extends ShayaDebugElement implements IDebugTarget {

	public static final String CURRENT_LINE_MARKER = "org.myau.shaya.ide.currentlinemarker";

	private final ILaunch launch;
	private final IProcess process;
	private final Process javaProcess;
	private final IFile file;
	private final ShayaThread thread;
	private final StringBuilder lineBuf = new StringBuilder();
	private volatile boolean terminated;
	private IFile highlightFile;
	private final Object evalLock = new Object();
	private volatile ShayaDebugEvent pendingEvalResult;

	public ShayaDebugTarget(ILaunch launch, IProcess process, Process javaProcess, IFile file) {
		super(null, launch);
		this.launch = launch;
		this.process = process;
		this.javaProcess = javaProcess;
		this.file = file;
		this.thread = new ShayaThread(this);
		fireEvent(DebugEvent.CREATE, DebugEvent.CLIENT_REQUEST);
		DebugPlugin.getDefault().getBreakpointManager().addBreakpointListener(this);
		installStreamListener();
		// Do NOT syncBreakpoints() here: stdin is shared with «ввод».
		// Breakpoints go via --break at launch; re-sync on each SHAYDBG stopped.
	}

	public IFile getProgramFile() {
		return file;
	}

	@Override
	public IDebugTarget getDebugTarget() {
		return this;
	}

	private void installStreamListener() {
		IStreamsProxy proxy = process.getStreamsProxy();
		if (proxy != null) {
			if (proxy.getOutputStreamMonitor() != null) {
				proxy.getOutputStreamMonitor().addListener((text, monitor) -> handleText(text));
			}
			if (proxy.getErrorStreamMonitor() != null) {
				proxy.getErrorStreamMonitor().addListener((text, monitor) -> handleText(text));
			}
		}
		new Thread(() -> {
			try {
				javaProcess.waitFor();
			} catch (InterruptedException e) {
				Thread.currentThread().interrupt();
			}
			terminated = true;
			clearHighlight();
			thread.onTerminated();
			DebugPlugin.getDefault().getBreakpointManager().removeBreakpointListener(this);
			fireEvent(DebugEvent.TERMINATE, DebugEvent.CLIENT_REQUEST);
		}, "shaya-debug-wait").start();
	}

	private void handleText(String text) {
		if (text == null || text.isEmpty()) {
			return;
		}
		synchronized (lineBuf) {
			lineBuf.append(text);
			int idx;
			while ((idx = indexOfNewline(lineBuf)) >= 0) {
				String line = lineBuf.substring(0, idx);
				lineBuf.delete(0, idx + 1);
				if (line.endsWith("\r")) {
					line = line.substring(0, line.length() - 1);
				}
				handleLine(line);
			}
		}
	}

	private static int indexOfNewline(StringBuilder buf) {
		for (int i = 0; i < buf.length(); i++) {
			if (buf.charAt(i) == '\n') {
				return i;
			}
		}
		return -1;
	}

	private void handleLine(String line) {
		ShayaDebugEvent ev = ShayaDebugEvent.parseLine(line);
		if (ev == null) {
			return;
		}
		if (ev.kind == ShayaDebugEvent.Kind.STOPPED) {
			highlightLine(ev.line, ev.path);
			thread.onStopped(ev);
			syncBreakpoints();
		} else if (ev.kind == ShayaDebugEvent.Kind.SET) {
			thread.onSet(ev);
		} else if (ev.kind == ShayaDebugEvent.Kind.EVAL) {
			synchronized (evalLock) {
				pendingEvalResult = ev;
				evalLock.notifyAll();
			}
		} else if (ev.kind == ShayaDebugEvent.Kind.TERMINATED) {
			terminated = true;
			clearHighlight();
			thread.onTerminated();
			synchronized (evalLock) {
				evalLock.notifyAll();
			}
			fireEvent(DebugEvent.TERMINATE, DebugEvent.CLIENT_REQUEST);
		}
	}

	/**
	 * Watch / Expressions: send {@code eval} and wait for {@code SHAYDBG} reply.
	 * Only while suspended (stdin shared with «ввод»).
	 */
	public String evaluate(String expr) throws DebugException {
		if (!isSuspended()) {
			throw new DebugException(new org.eclipse.core.runtime.Status(
					org.eclipse.core.runtime.IStatus.ERROR, Activator.PLUGIN_ID,
					"eval requires a suspended ALG step-debug session"));
		}
		String e = expr == null ? "" : expr.trim();
		if (e.isEmpty()) {
			return "";
		}
		synchronized (evalLock) {
			pendingEvalResult = null;
			writeCommand("{\"cmd\":\"eval\",\"expr\":\"" + ShayaJson.escapeString(e) + "\"}");
			long deadline = System.currentTimeMillis() + 8000;
			while (pendingEvalResult == null && !isTerminated()) {
				long left = deadline - System.currentTimeMillis();
				if (left <= 0) {
					break;
				}
				try {
					evalLock.wait(left);
				} catch (InterruptedException ie) {
					Thread.currentThread().interrupt();
					break;
				}
			}
			ShayaDebugEvent r = pendingEvalResult;
			pendingEvalResult = null;
			if (r == null) {
				throw new DebugException(new org.eclipse.core.runtime.Status(
						org.eclipse.core.runtime.IStatus.ERROR, Activator.PLUGIN_ID,
						"eval timeout"));
			}
			if (!r.evalOk) {
				String err = r.evalError == null || r.evalError.isEmpty() ? "eval failed" : r.evalError;
				throw new DebugException(new org.eclipse.core.runtime.Status(
						org.eclipse.core.runtime.IStatus.ERROR, Activator.PLUGIN_ID, err));
			}
			return r.evalValue == null ? "null" : r.evalValue;
		}
	}

	void step() throws DebugException {
		writeCommand("{\"cmd\":\"step\"}");
	}

	void stepInto() throws DebugException {
		writeCommand("{\"cmd\":\"step_into\"}");
	}

	void stepOut() throws DebugException {
		writeCommand("{\"cmd\":\"step_out\"}");
	}

	void cont() throws DebugException {
		writeCommand("{\"cmd\":\"continue\"}");
	}

	void setVariable(String name, String valueExpr) throws DebugException {
		writeCommand("{\"cmd\":\"set\",\"name\":\"" + ShayaJson.escapeString(name)
				+ "\",\"value\":\"" + ShayaJson.escapeString(valueExpr) + "\"}");
	}

	void syncBreakpoints() {
		try {
			writeCommand(ShayaBreakpoints.toProtocolCommand(file));
		} catch (DebugException ignored) {
		}
	}

	private void writeCommand(String json) throws DebugException {
		IStreamsProxy proxy = process.getStreamsProxy();
		if (proxy == null) {
			notSupported("write");
		}
		try {
			proxy.write(json + "\n");
		} catch (IOException e) {
			throw new DebugException(new org.eclipse.core.runtime.Status(
					org.eclipse.core.runtime.IStatus.ERROR,
					Activator.PLUGIN_ID,
					"Failed to send ALG debug command",
					e));
		}
	}

	private void highlightLine(Integer line, String path) {
		clearHighlight();
		if (line == null || line < 1) {
			return;
		}
		IFile target = ShayaSourceReveal.resolve(file, path);
		if (target == null || !target.exists()) {
			// Outside workspace (or unresolved): open via FileStore / launch fallback
			ShayaSourceReveal.reveal(file, path, line.intValue());
			return;
		}
		highlightFile = target;
		ShayaSourceReveal.reveal(file, path, line.intValue());
		try {
			IMarker m = target.createMarker(CURRENT_LINE_MARKER);
			m.setAttribute(IMarker.LINE_NUMBER, line);
			m.setAttribute(IMarker.MESSAGE, "ALG debug: current line " + line);
			m.setAttribute(IMarker.SEVERITY, IMarker.SEVERITY_INFO);
			if (target.getLocation() != null) {
				String contents = new String(
						Files.readAllBytes(Paths.get(target.getLocation().toOSString())),
						StandardCharsets.UTF_8);
				int start = offsetOfLine(contents, line);
				if (start >= 0) {
					int end = contents.indexOf('\n', start);
					if (end < 0) {
						end = contents.length();
					}
					m.setAttribute(IMarker.CHAR_START, Integer.valueOf(start));
					m.setAttribute(IMarker.CHAR_END, Integer.valueOf(end));
				}
			}
		} catch (Exception ignored) {
		}
	}

	private static int offsetOfLine(String contents, int line1) {
		if (line1 <= 1) {
			return 0;
		}
		int at = 0;
		int current = 1;
		while (current < line1 && at < contents.length()) {
			int nl = contents.indexOf('\n', at);
			if (nl < 0) {
				return -1;
			}
			at = nl + 1;
			current++;
		}
		return current == line1 ? at : -1;
	}

	private void clearHighlight() {
		IFile[] targets = new IFile[] { file, highlightFile };
		highlightFile = null;
		for (IFile f : targets) {
			if (f == null) {
				continue;
			}
			try {
				f.deleteMarkers(CURRENT_LINE_MARKER, true, IResource.DEPTH_ZERO);
			} catch (Exception ignored) {
			}
		}
	}

	@Override
	public boolean canTerminate() {
		return !isTerminated();
	}

	@Override
	public boolean isTerminated() {
		return terminated || process.isTerminated();
	}

	@Override
	public void terminate() throws DebugException {
		try {
			writeCommand("{\"cmd\":\"quit\"}");
		} catch (DebugException ignored) {
		}
		process.terminate();
		terminated = true;
		clearHighlight();
		thread.onTerminated();
		DebugPlugin.getDefault().getBreakpointManager().removeBreakpointListener(this);
		fireEvent(DebugEvent.TERMINATE, DebugEvent.CLIENT_REQUEST);
	}

	@Override
	public boolean canResume() {
		return thread.canResume();
	}

	@Override
	public boolean canSuspend() {
		return false;
	}

	@Override
	public boolean isSuspended() {
		return thread.isSuspended();
	}

	@Override
	public void resume() throws DebugException {
		thread.resume();
	}

	@Override
	public void suspend() throws DebugException {
		notSupported("suspend");
	}

	@Override
	public boolean canDisconnect() {
		return false;
	}

	@Override
	public void disconnect() throws DebugException {
		notSupported("disconnect");
	}

	@Override
	public boolean isDisconnected() {
		return false;
	}

	@Override
	public boolean supportsStorageRetrieval() {
		return false;
	}

	@Override
	public IMemoryBlock getMemoryBlock(long startAddress, long length) throws DebugException {
		return null;
	}

	@Override
	public IProcess getProcess() {
		return process;
	}

	@Override
	public IThread[] getThreads() {
		if (isTerminated()) {
			return new IThread[0];
		}
		return new IThread[] { thread };
	}

	@Override
	public boolean hasThreads() {
		return !isTerminated();
	}

	@Override
	public String getName() {
		return "ALG" + (file != null ? ": " + file.getName() : "");
	}

	@Override
	public boolean supportsBreakpoint(IBreakpoint breakpoint) {
		return breakpoint != null
				&& ShayaDebugElement.MODEL_ID.equals(breakpoint.getModelIdentifier());
	}

	@Override
	public void breakpointAdded(IBreakpoint breakpoint) {
		if (supportsBreakpoint(breakpoint) && thread.isSuspended()) {
			syncBreakpoints();
		}
	}

	@Override
	public void breakpointRemoved(IBreakpoint breakpoint, org.eclipse.core.resources.IMarkerDelta delta) {
		if (supportsBreakpoint(breakpoint) && thread.isSuspended()) {
			syncBreakpoints();
		}
	}

	@Override
	public void breakpointChanged(IBreakpoint breakpoint, org.eclipse.core.resources.IMarkerDelta delta) {
		if (supportsBreakpoint(breakpoint) && thread.isSuspended()) {
			syncBreakpoints();
		}
	}
}
