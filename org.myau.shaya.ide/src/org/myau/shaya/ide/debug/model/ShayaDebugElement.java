package org.myau.shaya.ide.debug.model;

import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.ILaunch;
import org.eclipse.debug.core.model.DebugElement;
import org.eclipse.debug.core.model.IDebugTarget;

/**
 * Базовый элемент модели отладки ALG.
 */
public abstract class ShayaDebugElement extends DebugElement {

	public static final String MODEL_ID = "org.myau.shaya.ide.debugModel";

	private final ILaunch launch;

	protected ShayaDebugElement(IDebugTarget target, ILaunch launch) {
		super(target);
		this.launch = launch;
	}

	@Override
	public String getModelIdentifier() {
		return MODEL_ID;
	}

	@Override
	public ILaunch getLaunch() {
		return launch;
	}

	protected void fireEvent(int kind, int detail) {
		DebugPlugin.getDefault().fireDebugEventSet(
				new org.eclipse.debug.core.DebugEvent[] {
						new org.eclipse.debug.core.DebugEvent(this, kind, detail)
				});
	}

	protected void notSupported(String op) throws DebugException {
		throw new DebugException(new org.eclipse.core.runtime.Status(
				org.eclipse.core.runtime.IStatus.ERROR,
				org.myau.shaya.ide.Activator.PLUGIN_ID,
				DebugException.NOT_SUPPORTED,
				op + " is not supported",
				null));
	}
}
