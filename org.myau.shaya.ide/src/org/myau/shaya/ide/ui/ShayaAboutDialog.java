package org.myau.shaya.ide.ui;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.osgi.util.NLS;
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
import org.myau.shaya.ide.i18n.Messages;
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
		newShell.setText(Messages.About_shellTitle);
	}

	@Override
	protected Control createDialogArea(Composite parent) {
		Composite area = (Composite) super.createDialogArea(parent);
		area.setLayout(new GridLayout(1, false));

		Label title = new Label(area, SWT.WRAP | SWT.CENTER);
		title.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		title.setText(Messages.About_title);

		Label body = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdBody = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdBody.widthHint = 380;
		gdBody.verticalIndent = 12;
		body.setLayoutData(gdBody);
		body.setText(Messages.About_body);

		Label cmds = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdCmds = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdCmds.widthHint = 380;
		gdCmds.verticalIndent = 10;
		cmds.setLayoutData(gdCmds);
		cmds.setText(Messages.About_cmds);

		Label meta = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdMeta = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdMeta.verticalIndent = 10;
		meta.setLayoutData(gdMeta);
		meta.setForeground(parent.getDisplay().getSystemColor(SWT.COLOR_DARK_GRAY));
		meta.setText(NLS.bind(Messages.About_meta, new Object[] {
				Activator.PLUGIN_ID, bundleVersion(), toolchainLine() }));

		Composite links = new Composite(area, SWT.NONE);
		links.setLayoutData(new GridData(SWT.CENTER, SWT.CENTER, true, false));
		links.setLayout(new GridLayout(2, true));
		Button mapBtn = new Button(links, SWT.PUSH);
		mapBtn.setText(Messages.About_grammarButton);
		mapBtn.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				java.io.File map = ShayaDocs.findExtensionMap();
				if (map != null && map.isFile()) {
					ShayaOpenMapHandler.openFile(map);
				} else {
					MessageDialog.openInformation(getShell(), Messages.About_grammarMissingTitle,
							Messages.About_grammarMissing);
				}
			}
		});
		Button trackBtn = new Button(links, SWT.PUSH);
		trackBtn.setText(Messages.About_trackButton);
		trackBtn.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				java.io.File track = ShayaDocs.findTrackReadme();
				if (track != null && track.isFile()) {
					ShayaOpenMapHandler.openFile(track);
				} else {
					MessageDialog.openInformation(getShell(), Messages.About_trackMissingTitle,
							Messages.About_trackMissing);
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
		return Messages.About_toolchainNotFound;
	}

	@Override
	protected void createButtonsForButtonBar(Composite parent) {
		createButton(parent, IDialogConstants.OK_ID, IDialogConstants.OK_LABEL, true);
	}
}
