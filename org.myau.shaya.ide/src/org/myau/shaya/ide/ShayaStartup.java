package org.myau.shaya.ide;

import org.eclipse.swt.widgets.Display;
import org.eclipse.ui.IEditorRegistry;
import org.eclipse.ui.IStartup;
import org.eclipse.ui.PlatformUI;

/**
 * Forces default editor association for {@code .alg}.
 * plugin.xml alone is not enough when the workspace already cached "Default Text Editor".
 */
public class ShayaStartup implements IStartup {

	private static final String[][] ASSOC = {
			{ "*.alg", "org.myau.shaya.ide.editor.alg" },
	};

	@Override
	public void earlyStartup() {
		Display.getDefault().asyncExec(() -> {
			if (!PlatformUI.isWorkbenchRunning()) {
				return;
			}
			IEditorRegistry reg = PlatformUI.getWorkbench().getEditorRegistry();
			for (String[] pair : ASSOC) {
				reg.setDefaultEditor(pair[0], pair[1]);
			}
		});
	}
}
