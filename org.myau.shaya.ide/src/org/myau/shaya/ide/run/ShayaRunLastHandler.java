package org.myau.shaya.ide.run;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.handlers.HandlerUtil;

/** Repeat the last ALG Run / Check / Transpile. */
public class ShayaRunLastHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		if (!ShayaLastLaunch.hasLast()) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG Run Last",
					"No previous Run / Check / Transpile yet.\n"
							+ "Use ALG → Run, Check, or Transpile once, then Ctrl+Alt+L.");
			return null;
		}
		ShayaSourceResolver.ResolvedSource src = ShayaLastLaunch.lastSource();
		if (src == null) {
			MessageDialog.openWarning(HandlerUtil.getActiveShell(event), "ALG Run Last",
					"Last file is missing:\n" + ShayaLastLaunch.describe());
			return null;
		}
		ShayaLastLaunch.Mode mode = ShayaLastLaunch.lastMode();
		if (mode == ShayaLastLaunch.Mode.CHECK) {
			ShayaLauncher.check(src.file, src.workspaceFile);
		} else if (mode == ShayaLastLaunch.Mode.TRANSPILE) {
			ShayaLauncher.transpile(src.file, src.workspaceFile);
		} else {
			ShayaLauncher.run(src.file, src.workspaceFile);
		}
		return null;
	}
}
