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
					"examples/track/README.md not found.\n"
							+ "Install dropins/schoolalgol-shaya (examples/) or open from the repository.");
			return null;
		}
		ShayaOpenMapHandler.openFile(readme);
		return null;
	}
}
