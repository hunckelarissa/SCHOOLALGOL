package org.myau.shaya.ide.run;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

public class ShayaRunHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		ShayaSourceResolver.ResolvedSource src = ShayaSourceResolver.resolveSource(event);
		if (src == null) {
			MessageDialog.openWarning(HandlerUtil.getActiveShell(event), "ALG",
					"Open or select a ALG source (" + ShayaToolchain.extensionsHint() + ").\n"
							+ "If the file is in a project folder but missing from Project Explorer: Refresh (F5).");
			return null;
		}
		IEditorPart editor = HandlerUtil.getActiveEditor(event);
		if (editor != null && editor.isDirty()) {
			editor.doSave(null);
		}
		ShayaLastLaunch.remember(ShayaLastLaunch.Mode.RUN, src);
		ShayaLauncher.run(src.file, src.workspaceFile);
		return null;
	}
}
