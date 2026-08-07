package org.myau.shaya.ide.ui;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.viewers.StructuredSelection;
import org.eclipse.jface.wizard.WizardDialog;
import org.eclipse.swt.SWT;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.handlers.IHandlerService;
import org.eclipse.ui.wizards.IWizardDescriptor;
import org.eclipse.ui.IWorkbenchWizard;

/**
 * Welcome — first-step CTAs for ALG / SCHOOLALGOL.
 */
public class ShayaWelcomeDialog extends Dialog {

	public static final int ID_NEW_PROJECT = IDialogConstants.CLIENT_ID + 1;
	public static final int ID_IMPORT_TRACK = IDialogConstants.CLIENT_ID + 2;
	public static final int ID_SHORTCUTS = IDialogConstants.CLIENT_ID + 3;

	private final Shell hostShell;

	public ShayaWelcomeDialog(Shell parentShell) {
		super(parentShell);
		this.hostShell = parentShell;
	}

	@Override
	protected void configureShell(Shell newShell) {
		super.configureShell(newShell);
		newShell.setText("Welcome — ALG");
	}

	@Override
	protected Control createDialogArea(Composite parent) {
		Composite area = (Composite) super.createDialogArea(parent);
		area.setLayout(new GridLayout(1, false));

		Label title = new Label(area, SWT.WRAP | SWT.CENTER);
		title.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		title.setText("ALG / SCHOOLALGOL");

		Label tip = new Label(area, SWT.WRAP | SWT.CENTER);
		GridData gdTip = new GridData(SWT.FILL, SWT.CENTER, true, false);
		gdTip.widthHint = 360;
		gdTip.verticalIndent = 10;
		tip.setLayoutData(gdTip);
		tip.setText("Файлы .alg → интерпретатор SCHOOLALGOL (School Algol).\n"
				+ "Начните с проекта, Hello.alg или шпаргалки клавиш.");

		return area;
	}

	@Override
	protected void createButtonsForButtonBar(Composite parent) {
		createButton(parent, ID_NEW_PROJECT, "New Project…", true);
		createButton(parent, ID_IMPORT_TRACK, "Import Track…", false);
		createButton(parent, ID_SHORTCUTS, "Shortcuts…", false);
		createButton(parent, IDialogConstants.CLOSE_ID, IDialogConstants.CLOSE_LABEL, false);
	}

	@Override
	protected void buttonPressed(int buttonId) {
		if (buttonId == ID_NEW_PROJECT || buttonId == ID_IMPORT_TRACK || buttonId == ID_SHORTCUTS) {
			setReturnCode(buttonId);
			close();
			runAction(buttonId);
			return;
		}
		if (buttonId == IDialogConstants.CLOSE_ID) {
			cancelPressed();
			return;
		}
		super.buttonPressed(buttonId);
	}

	private void runAction(int buttonId) {
		Shell shell = hostShell != null ? hostShell : getParentShell();
		try {
			if (buttonId == ID_NEW_PROJECT) {
				openNewProjectWizard(shell);
			} else if (buttonId == ID_IMPORT_TRACK) {
				IHandlerService hs = PlatformUI.getWorkbench().getService(IHandlerService.class);
				if (hs != null) {
					hs.executeCommand("org.myau.shaya.ide.commands.importTrack", null);
				}
			} else if (buttonId == ID_SHORTCUTS) {
				new ShayaShortcutsDialog(shell).open();
			}
		} catch (Exception e) {
			org.eclipse.jface.dialogs.MessageDialog.openError(shell, "Welcome",
					e.getMessage() != null ? e.getMessage() : String.valueOf(e));
		}
	}

	static void openNewProjectWizard(Shell shell) throws Exception {
		IWizardDescriptor desc = PlatformUI.getWorkbench().getNewWizardRegistry()
				.findWizard("org.myau.shaya.ide.wizards.newProject");
		if (desc == null) {
			org.eclipse.jface.dialogs.MessageDialog.openInformation(shell, "Welcome",
					"ALG Project wizard not found.\nUse File → New → Project → ALG.");
			return;
		}
		IWorkbenchWizard wizard = desc.createWizard();
		wizard.init(PlatformUI.getWorkbench(), StructuredSelection.EMPTY);
		new WizardDialog(shell, wizard).open();
	}
}
