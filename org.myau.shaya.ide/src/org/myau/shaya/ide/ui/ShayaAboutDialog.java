package org.myau.shaya.ide.ui;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.run.ShayaOpenMapHandler;
import org.myau.shaya.ide.toolchain.ShayaDocs;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * About ALG / SCHOOLALGOL.
 */
public class ShayaAboutDialog extends Dialog {

	public ShayaAboutDialog(Shell parentShell) {
		super(parentShell);
	}

	@Override
	protected void configureShell(Shell newShell) {
		super.configureShell(newShell);
		newShell.setText("About ALG");
	}

	@Override
	protected Control createDialogArea(Composite parent) {
		Composite area = (Composite) super.createDialogArea(parent);
		area.setLayout(new GridLayout(1, false));

		Label title = new Label(area, SWT.WRAP | SWT.CENTER);
		title.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		title.setText("ALG — School Algol IDE\nSCHOOLALGOL (.alg)");

		Label body = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdBody = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdBody.widthHint = 380;
		gdBody.verticalIndent = 12;
		body.setLayoutData(gdBody);
		body.setText(
				"Eclipse-плагин для редактирования и запуска программ\n"
						+ "на школьном алгоритмическом языке School Algol.\n\n"
						+ "Файлы .alg выполняются интерпретатором SCHOOLALGOL\n"
						+ "(Python, main.py в toolchain dropins).");

		Label cmds = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdCmds = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdCmds.widthHint = 380;
		gdCmds.verticalIndent = 10;
		cmds.setLayoutData(gdCmds);
		cmds.setText(
				"Run — выполнить программу\n"
						+ "Check — синтаксическая проверка (lex + parse)\n"
						+ "Step Debug — пошаговая отладка (SHAYDBG)\n"
						+ "Ctrl+Alt+Shift+D — горячая клавиша Step Debug");

		Label meta = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdMeta = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdMeta.verticalIndent = 10;
		meta.setLayoutData(gdMeta);
		meta.setForeground(parent.getDisplay().getSystemColor(SWT.COLOR_DARK_GRAY));
		meta.setText("Plugin: " + Activator.PLUGIN_ID
				+ " " + bundleVersion() + "\nToolchain: " + toolchainLine());

		Composite links = new Composite(area, SWT.NONE);
		links.setLayoutData(new GridData(SWT.CENTER, SWT.CENTER, true, false));
		links.setLayout(new GridLayout(2, true));
		Button mapBtn = new Button(links, SWT.PUSH);
		mapBtn.setText("Грамматика…");
		mapBtn.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				java.io.File map = ShayaDocs.findExtensionMap();
				if (map != null && map.isFile()) {
					ShayaOpenMapHandler.openFile(map);
				} else {
					MessageDialog.openInformation(getShell(), "Грамматика",
							"GRAMMAR.md не найден.\n\n"
									+ "Запустите в репозитории:\n"
									+ "  .\\install_dropins.ps1\n"
									+ "(копирует GRAMMAR.md в schoolalgol-shaya\\docs\\)\n"
									+ "или откройте GRAMMAR.md из корня SCHOOLALGOL.");
				}
			}
		});
		Button trackBtn = new Button(links, SWT.PUSH);
		trackBtn.setText("Учебный трек…");
		trackBtn.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				java.io.File track = ShayaDocs.findTrackReadme();
				if (track != null && track.isFile()) {
					ShayaOpenMapHandler.openFile(track);
				} else {
					MessageDialog.openInformation(getShell(), "Учебный трек",
							"examples/track/README.md не найден.\n\n"
									+ "Запустите:\n"
									+ "  .\\install_dropins.ps1 -Examples\n"
									+ "или откройте examples/track/ из репозитория.");
				}
			}
		});

		return area;
	}

	private static String bundleVersion() {
		try {
			if (Activator.getDefault() != null && Activator.getDefault().getBundle() != null) {
				return Activator.getDefault().getBundle().getVersion().toString();
			}
		} catch (Exception ignored) {
		}
		return "?";
	}

	private static String toolchainLine() {
		try {
			java.io.File home = ShayaToolchain.getToolchainHome();
			if (home != null) {
				return home.getAbsolutePath();
			}
		} catch (Exception ignored) {
		}
		return "(не найден — Preferences → ALG)";
	}

	@Override
	protected void createButtonsForButtonBar(Composite parent) {
		createButton(parent, IDialogConstants.OK_ID, IDialogConstants.OK_LABEL, true);
	}
}
