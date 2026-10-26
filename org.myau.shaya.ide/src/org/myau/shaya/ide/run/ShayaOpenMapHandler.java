package org.myau.shaya.ide.run;

import java.io.File;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.filesystem.EFS;
import org.eclipse.core.filesystem.IFileStore;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.program.Program;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.ide.IDE;
import org.myau.shaya.ide.i18n.Messages;
import org.myau.shaya.ide.toolchain.ShayaDocs;

/** Open GRAMMAR.md / GRAMMAR.ru.md (description of the .alg language). */
public class ShayaOpenMapHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		File map = ShayaDocs.findExtensionMap();
		if (map == null || !map.isFile()) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), Messages.Grammar_title,
					Messages.Grammar_missing);
			return null;
		}
		openFile(map);
		return null;
	}

	public static void openFile(File file) {
		try {
			IWorkbenchPage page = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage();
			IFileStore store = EFS.getLocalFileSystem().fromLocalFile(file);
			IDE.openEditorOnFileStore(page, store);
		} catch (Exception e) {
			Program.launch(file.getAbsolutePath());
		}
	}
}
