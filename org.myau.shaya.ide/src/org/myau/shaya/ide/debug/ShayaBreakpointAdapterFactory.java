package org.myau.shaya.ide.debug;

import org.eclipse.core.runtime.IAdapterFactory;
import org.eclipse.debug.ui.actions.IToggleBreakpointsTarget;
import org.myau.shaya.ide.editor.ShayaEditor;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Adapter: ALG editor → toggle line breakpoints (Ctrl+Shift+B).
 * Only for engines with step-debug protocol ({@code supportsStepDebugUi}).
 */
public class ShayaBreakpointAdapterFactory implements IAdapterFactory {

	@Override
	@SuppressWarnings("unchecked")
	public <T> T getAdapter(Object adaptableObject, Class<T> adapterType) {
		if (!IToggleBreakpointsTarget.class.equals(adapterType)) {
			return null;
		}
		if (!(adaptableObject instanceof ShayaEditor)) {
			return null;
		}
		ShayaEditor editor = (ShayaEditor) adaptableObject;
		String name = editor.getEditorInput() != null ? editor.getEditorInput().getName() : null;
		String engine = ShayaToolchain.engineIdForName(name);
		if (!ShayaToolchain.supportsStepDebugUi(engine)) {
			return null;
		}
		return (T) new ShayaToggleBreakpointsTarget();
	}

	@Override
	public Class<?>[] getAdapterList() {
		return new Class<?>[] { IToggleBreakpointsTarget.class };
	}
}
