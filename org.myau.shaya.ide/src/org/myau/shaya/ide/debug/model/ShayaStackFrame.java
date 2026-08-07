package org.myau.shaya.ide.debug.model;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.model.IRegisterGroup;
import org.eclipse.debug.core.model.IStackFrame;
import org.eclipse.debug.core.model.IThread;
import org.eclipse.debug.core.model.IVariable;
import org.myau.shaya.ide.debug.ShayaDebugEvent;

/**
 * Стек-фрейм ALG.
 */
public class ShayaStackFrame extends ShayaDebugElement implements IStackFrame {

	private final ShayaThread thread;
	private final String name;
	private final Integer line;
	private final String source;
	private final String path;
	private IVariable[] variables = new IVariable[0];
	private Map<String, String> previousValues = new LinkedHashMap<>();

	public ShayaStackFrame(ShayaDebugTarget target, ShayaThread thread, String name, Integer line) {
		this(target, thread, name, line, "", "");
	}

	public ShayaStackFrame(ShayaDebugTarget target, ShayaThread thread, String name, Integer line, String source) {
		this(target, thread, name, line, source, "");
	}

	public ShayaStackFrame(ShayaDebugTarget target, ShayaThread thread, String name, Integer line, String source,
			String path) {
		super(target, target.getLaunch());
		this.thread = thread;
		this.name = name == null || name.isEmpty() ? "main" : name;
		this.line = line;
		this.source = source == null ? "" : source;
		this.path = path == null ? "" : path;
	}

	public String getPath() {
		return path;
	}

	public void setPreviousValues(Map<String, String> previous) {
		this.previousValues = previous == null ? new LinkedHashMap<>() : new LinkedHashMap<>(previous);
	}

	public Map<String, String> snapshotValues() {
		Map<String, String> snap = new LinkedHashMap<>();
		for (IVariable v : variables) {
			if (v instanceof ShayaVariable) {
				ShayaVariable sv = (ShayaVariable) v;
				snap.put(sv.getName(), sv.getValueText());
			}
		}
		return snap;
	}

	public void updateVariables(ShayaDebugEvent event) {
		List<IVariable> list = new ArrayList<>();
		ShayaDebugTarget target = (ShayaDebugTarget) getDebugTarget();
		if (event.locals != null) {
			for (Map.Entry<String, Object> e : event.locals.entrySet()) {
				String key = "local." + e.getKey();
				String flat = ShayaDebugEvent.stringify(e.getValue());
				boolean changed = previousValues.containsKey(key) && !previousValues.get(key).equals(flat);
				list.add(ShayaVariable.fromProtocol(target, key, e.getValue(), changed));
			}
		}
		if (event.globals != null) {
			for (Map.Entry<String, Object> e : event.globals.entrySet()) {
				String key = e.getKey();
				String flat = ShayaDebugEvent.stringify(e.getValue());
				boolean changed = previousValues.containsKey(key) && !previousValues.get(key).equals(flat);
				list.add(ShayaVariable.fromProtocol(target, key, e.getValue(), changed));
			}
		}
		if (event.arrays != null) {
			for (Map.Entry<String, Object> e : event.arrays.entrySet()) {
				String key = "arr." + e.getKey();
				String flat = ShayaDebugEvent.stringify(e.getValue());
				boolean changed = previousValues.containsKey(key) && !previousValues.get(key).equals(flat);
				list.add(ShayaVariable.fromProtocol(target, key, e.getValue(), changed));
			}
		}
		if (event.records != null) {
			for (Map.Entry<String, Object> e : event.records.entrySet()) {
				String key = "rec." + e.getKey();
				String flat = ShayaDebugEvent.stringify(e.getValue());
				boolean changed = previousValues.containsKey(key) && !previousValues.get(key).equals(flat);
				list.add(ShayaVariable.fromProtocol(target, key, e.getValue(), changed));
			}
		}
		variables = list.toArray(new IVariable[0]);
	}

	@Override
	public boolean canStepInto() {
		return getThread().canStepInto();
	}

	@Override
	public boolean canStepOver() {
		return getThread().canStepOver();
	}

	@Override
	public boolean canStepReturn() {
		return getThread().canStepReturn();
	}

	@Override
	public boolean isStepping() {
		return getThread().isStepping();
	}

	@Override
	public void stepInto() throws DebugException {
		getThread().stepInto();
	}

	@Override
	public void stepOver() throws DebugException {
		getThread().stepOver();
	}

	@Override
	public void stepReturn() throws DebugException {
		getThread().stepReturn();
	}

	@Override
	public boolean canResume() {
		return getThread().canResume();
	}

	@Override
	public boolean canSuspend() {
		return false;
	}

	@Override
	public boolean isSuspended() {
		return getThread().isSuspended();
	}

	@Override
	public void resume() throws DebugException {
		getThread().resume();
	}

	@Override
	public void suspend() throws DebugException {
		notSupported("suspend");
	}

	@Override
	public boolean canTerminate() {
		return getThread().canTerminate();
	}

	@Override
	public boolean isTerminated() {
		return getThread().isTerminated();
	}

	@Override
	public void terminate() throws DebugException {
		getThread().terminate();
	}

	@Override
	public IThread getThread() {
		return thread;
	}

	@Override
	public IVariable[] getVariables() {
		return variables;
	}

	@Override
	public boolean hasVariables() {
		return variables.length > 0;
	}

	@Override
	public int getLineNumber() {
		return line == null ? -1 : line.intValue();
	}

	public String getSourceLine() {
		return source;
	}

	@Override
	public int getCharStart() {
		return -1;
	}

	@Override
	public int getCharEnd() {
		return -1;
	}

	@Override
	public String getName() {
		return name + (line == null ? "" : " [line " + line + "]");
	}

	@Override
	public IRegisterGroup[] getRegisterGroups() {
		return new IRegisterGroup[0];
	}

	@Override
	public boolean hasRegisterGroups() {
		return false;
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T> T getAdapter(Class<T> adapter) {
		if (adapter == IFile.class || adapter == IResource.class) {
			IFile prog = ((ShayaDebugTarget) getDebugTarget()).getProgramFile();
			IFile f = org.myau.shaya.ide.debug.ShayaSourceReveal.resolve(prog, path);
			if (f != null) {
				return (T) f;
			}
		}
		return super.getAdapter(adapter);
	}
}
