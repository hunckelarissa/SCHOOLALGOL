package org.myau.shaya.ide;

import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorRegistry;
import org.eclipse.ui.IStartup;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.myau.shaya.ide.prefs.ShayaPreferenceConstants;
import org.myau.shaya.ide.ui.ShayaWelcomeDialog;

/**
 * Forces default editor association for {@code .alg}.
 * plugin.xml alone is not enough when the workspace already cached "Default Text Editor".
 * Also shows first-run Welcome once.
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
			maybeShowWelcome();
		});
	}

	private static void maybeShowWelcome() {
		try {
			if (Activator.getDefault() == null) {
				return;
			}
			IPreferenceStore store = Activator.getDefault().getPreferenceStore();
			if (!store.getBoolean(ShayaPreferenceConstants.SHOW_WELCOME_ON_STARTUP)) {
				return;
			}
			IWorkbenchWindow window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
			if (window == null) {
				return;
			}
			Shell shell = window.getShell();
			if (shell == null || shell.isDisposed()) {
				return;
			}
			store.setValue(ShayaPreferenceConstants.SHOW_WELCOME_ON_STARTUP, false);
			new ShayaWelcomeDialog(shell).open();
		} catch (Exception ignored) {
		}
	}
}
