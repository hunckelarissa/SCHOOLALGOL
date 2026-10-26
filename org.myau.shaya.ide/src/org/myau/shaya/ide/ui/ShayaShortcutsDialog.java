package org.myau.shaya.ide.ui;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.StyledText;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.graphics.FontData;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Shell;
import org.myau.shaya.ide.i18n.Messages;

/** Scrollable keyboard shortcuts cheat sheet. */
public class ShayaShortcutsDialog extends Dialog {

	private Font mono;

	public ShayaShortcutsDialog(Shell parentShell) {
		super(parentShell);
		setShellStyle(getShellStyle() | SWT.RESIZE | SWT.MAX);
	}

	@Override
	protected void configureShell(Shell newShell) {
		super.configureShell(newShell);
		newShell.setText(Messages.Shortcuts_shellTitle);
		newShell.setMinimumSize(480, 420);
	}

	@Override
	protected Control createDialogArea(Composite parent) {
		Composite area = (Composite) super.createDialogArea(parent);
		area.setLayout(new GridLayout(1, false));

		StyledText text = new StyledText(area, SWT.BORDER | SWT.V_SCROLL | SWT.H_SCROLL | SWT.READ_ONLY | SWT.MULTI | SWT.WRAP);
		GridData gd = new GridData(SWT.FILL, SWT.FILL, true, true);
		gd.widthHint = 520;
		gd.heightHint = 420;
		text.setLayoutData(gd);
		text.setText(Messages.Shortcuts_body);
		text.setEditable(false);
		FontData[] fds = text.getFont().getFontData();
		for (FontData fd : fds) {
			fd.setHeight(Math.max(9, fd.getHeight()));
			fd.setName("Consolas");
		}
		mono = new Font(parent.getDisplay(), fds);
		text.setFont(mono);
		return area;
	}

	@Override
	protected void createButtonsForButtonBar(Composite parent) {
		createButton(parent, IDialogConstants.OK_ID, IDialogConstants.CLOSE_LABEL, true);
	}

	@Override
	public boolean close() {
		if (mono != null && !mono.isDisposed()) {
			mono.dispose();
			mono = null;
		}
		return super.close();
	}
}
