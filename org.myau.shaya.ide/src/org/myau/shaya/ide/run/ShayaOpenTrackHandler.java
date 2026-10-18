package org.myau.shaya.ide.run;

import java.io.File;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.handlers.HandlerUtil;
import org.myau.shaya.ide.toolchain.ShayaDocs;

/** Open examples/track/README.md (учебный трек). */
public class ShayaOpenTrackHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		File readme = ShayaDocs.findTrackReadme();
		if (readme == null || !readme.isFile()) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "Учебный трек",
					"examples/track/README.md не найден.\n\n"
							+ "Что сделать:\n"
							+ "1. .\\install_dropins.ps1 -Examples\n"
							+ "2. Или откройте examples/track/ из репозитория SCHOOLALGOL.\n"
							+ "3. Preferences → ALG → Toolchain home = schoolalgol-shaya.");
			return null;
		}
		ShayaOpenMapHandler.openFile(readme);
		return null;
	}
}
