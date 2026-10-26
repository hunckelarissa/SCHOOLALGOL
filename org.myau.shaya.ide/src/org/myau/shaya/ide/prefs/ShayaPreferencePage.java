package org.myau.shaya.ide.prefs;

import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.preference.BooleanFieldEditor;
import org.eclipse.jface.preference.DirectoryFieldEditor;
import org.eclipse.jface.preference.FieldEditorPreferencePage;
import org.eclipse.jface.preference.FileFieldEditor;
import org.eclipse.jface.preference.IntegerFieldEditor;
import org.eclipse.jface.preference.StringFieldEditor;
import org.eclipse.osgi.util.NLS;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchPreferencePage;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.i18n.Messages;
import org.myau.shaya.ide.run.ShayaLastLaunch;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Preferences → ALG
 */
public class ShayaPreferencePage extends FieldEditorPreferencePage implements IWorkbenchPreferencePage {

	public ShayaPreferencePage() {
		super(GRID);
		setPreferenceStore(Activator.getDefault().getPreferenceStore());
		setDescription(NLS.bind(Messages.Prefs_description,
				ShayaToolchain.DROPINS_FOLDER, ShayaToolchain.ENGINE_DIR));
	}

	@Override
	public void init(IWorkbench workbench) {
	}

	@Override
	protected void createFieldEditors() {
		addField(new DirectoryFieldEditor(
				ShayaPreferenceConstants.TOOLCHAIN_HOME,
				NLS.bind(Messages.Prefs_toolchainHome, ShayaToolchain.DROPINS_FOLDER),
				getFieldEditorParent()));
		addField(new StringFieldEditor(
				ShayaPreferenceConstants.EXTRA_ARGS,
				Messages.Prefs_extraArgs,
				getFieldEditorParent()));
		addField(new FileFieldEditor(
				ShayaPreferenceConstants.PYTHON_EXECUTABLE,
				Messages.Prefs_python,
				getFieldEditorParent()));
		IntegerFieldEditor indent = new IntegerFieldEditor(
				ShayaPreferenceConstants.INDENT_WIDTH,
				Messages.Prefs_indentWidth,
				getFieldEditorParent());
		indent.setValidRange(2, 4);
		addField(indent);
		addField(new BooleanFieldEditor(
				ShayaPreferenceConstants.INSERT_SPACES,
				Messages.Prefs_insertSpaces,
				getFieldEditorParent()));
		addField(new BooleanFieldEditor(
				ShayaPreferenceConstants.CHECK_ON_SAVE,
				Messages.Prefs_checkOnSave,
				getFieldEditorParent()));
		addField(new BooleanFieldEditor(
				ShayaPreferenceConstants.SHOW_WELCOME_ON_STARTUP,
				Messages.Prefs_showWelcome,
				getFieldEditorParent()));
	}

	@Override
	protected void contributeButtons(Composite parent) {
		super.contributeButtons(parent);
		((GridLayout) parent.getLayout()).numColumns += 2;

		Button validate = new Button(parent, SWT.PUSH);
		validate.setText(Messages.Prefs_validateButton);
		validate.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
		validate.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				performApply();
				String status = ShayaToolchain.validateStatus();
				boolean ok = !(status.contains("ERROR") || status.contains("ОШИБКА"));
				if (ok) {
					MessageDialog.openInformation(getShell(), Messages.Prefs_validateTitle, status);
				} else {
					MessageDialog.openWarning(getShell(), Messages.Prefs_validateTitle, status);
				}
			}
		});

		Button clear = new Button(parent, SWT.PUSH);
		clear.setText(Messages.Prefs_clearRecentButton);
		clear.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
		clear.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				ShayaLastLaunch.clearHistory();
				MessageDialog.openInformation(getShell(), Messages.Prefs_clearTitle,
						Messages.Prefs_clearMessage);
			}
		});
	}
}
