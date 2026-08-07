package org.myau.shaya.ide.ui;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.ui.handlers.HandlerUtil;

/** Opens About ALG IDE dialog. */
public class ShayaAboutHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		ShayaAboutDialog dialog = new ShayaAboutDialog(HandlerUtil.getActiveShell(event));
		dialog.open();
		return null;
	}
}
