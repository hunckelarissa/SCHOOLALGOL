package org.myau.shaya.ide.run;

import java.util.ArrayList;
import java.util.List;

import org.eclipse.core.filesystem.EFS;
import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.ActionContributionItem;
import org.eclipse.jface.action.IContributionItem;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.actions.CompoundContributionItem;
import org.eclipse.ui.ide.IDE;

/**
 * ALG → Recent — open last files (persisted). Re-run via Run Last.
 */
public class ShayaRecentContribution extends CompoundContributionItem {

	@Override
	protected IContributionItem[] getContributionItems() {
		List<ShayaLastLaunch.Entry> recent = ShayaLastLaunch.recent();
		List<IContributionItem> items = new ArrayList<>();
		if (recent.isEmpty()) {
			Action empty = new Action("(no recent runs)") {
				@Override
				public void run() {
				}
			};
			empty.setEnabled(false);
			items.add(new ActionContributionItem(empty));
			return items.toArray(new IContributionItem[0]);
		}
		int n = 0;
		for (ShayaLastLaunch.Entry e : recent) {
			final ShayaLastLaunch.Entry entry = e;
			final int idx = ++n;
			Action a = new Action(idx + ". " + entry.label()) {
				@Override
				public void run() {
					openOnly(entry);
				}
			};
			a.setToolTipText(entry.diskPath + "\n(Open only — use Run Last to re-run)");
			items.add(new ActionContributionItem(a));
		}
		items.add(new Separator());
		Action clear = new Action("Clear Recent") {
			@Override
			public void run() {
				ShayaLastLaunch.clearHistory();
				MessageDialog.openInformation(
						PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
						"ALG Recent",
						"Recent list cleared.");
			}
		};
		items.add(new ActionContributionItem(clear));
		return items.toArray(new IContributionItem[0]);
	}

	private static void openOnly(ShayaLastLaunch.Entry entry) {
		ShayaSourceResolver.ResolvedSource src = ShayaLastLaunch.toSource(entry);
		if (src == null) {
			MessageDialog.openWarning(
					PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
					"ALG Recent",
					"File missing:\n" + entry.diskPath);
			return;
		}
		try {
			if (src.workspaceFile != null && src.workspaceFile.exists()) {
				IDE.openEditor(
						PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage(),
						src.workspaceFile);
			} else {
				IDE.openEditorOnFileStore(
						PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage(),
						EFS.getLocalFileSystem().fromLocalFile(src.file));
			}
		} catch (Exception ex) {
			MessageDialog.openWarning(
					PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
					"ALG Recent",
					"Could not open:\n" + entry.diskPath + "\n" + ex.getMessage());
		}
	}
}
