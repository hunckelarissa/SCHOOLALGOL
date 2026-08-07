package org.myau.shaya.ide.debug.model;

import org.eclipse.core.resources.IFile;
import org.eclipse.debug.core.model.ISourceLocator;
import org.eclipse.debug.core.model.IStackFrame;
import org.myau.shaya.ide.debug.ShayaSourceReveal;

/**
 * Source locator: стек-фрейм → файл по {@code path} из SHAYDBG (fallback — файл запуска).
 */
public class ShayaSourceLocator implements ISourceLocator {

	private final IFile programFile;

	public ShayaSourceLocator(IFile programFile) {
		this.programFile = programFile;
	}

	@Override
	public Object getSourceElement(IStackFrame stackFrame) {
		if (stackFrame instanceof ShayaStackFrame) {
			ShayaStackFrame sf = (ShayaStackFrame) stackFrame;
			IFile prog = ((ShayaDebugTarget) stackFrame.getDebugTarget()).getProgramFile();
			if (prog == null) {
				prog = programFile;
			}
			IFile resolved = ShayaSourceReveal.resolve(prog, sf.getPath());
			return resolved != null ? resolved : prog;
		}
		return programFile;
	}

	public IFile getProgramFile() {
		return programFile;
	}
}
