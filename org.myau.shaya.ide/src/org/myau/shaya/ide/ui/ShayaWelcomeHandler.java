package org.myau.shaya.ide.ui;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.WorkbenchException;
import org.eclipse.ui.handlers.HandlerUtil;

/**
 * Welcome: open ALG perspective and show first-step dialog.
 */
public class ShayaWelcomeHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		Shell shell = HandlerUtil.getActiveShell(event);
		openPerspective();
		if (shell != null) {
			new ShayaWelcomeDialog(shell).open();
		}
		return null;
	}

	private static void openPerspective() {
		try {
			IWorkbench wb = PlatformUI.getWorkbench();
			IWorkbenchWindow win = wb.getActiveWorkbenchWindow();
			if (win != null) {
				wb.showPerspective(ShayaPerspectiveFactory.ID, win);
			}
		} catch (WorkbenchException ignored) {
		}
	}
}
