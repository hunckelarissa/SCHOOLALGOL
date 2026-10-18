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
import org.myau.shaya.ide.toolchain.ShayaDocs;

/** Open GRAMMAR.md (описание языка .alg). */
public class ShayaOpenMapHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		File map = ShayaDocs.findExtensionMap();
		if (map == null || !map.isFile()) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "Грамматика",
					"GRAMMAR.md не найден.\n\n"
							+ "Что сделать:\n"
							+ "1. В репозитории SCHOOLALGOL: .\\install_dropins.ps1\n"
							+ "   (копирует GRAMMAR.md → schoolalgol-shaya\\docs\\)\n"
							+ "2. Или откройте GRAMMAR.md из корня репозитория.\n"
							+ "3. Проверьте Preferences → ALG → Toolchain home.");
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
