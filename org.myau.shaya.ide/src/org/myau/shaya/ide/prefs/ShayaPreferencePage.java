package org.myau.shaya.ide.prefs;

import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.preference.BooleanFieldEditor;
import org.eclipse.jface.preference.DirectoryFieldEditor;
import org.eclipse.jface.preference.FieldEditorPreferencePage;
import org.eclipse.jface.preference.FileFieldEditor;
import org.eclipse.jface.preference.IntegerFieldEditor;
import org.eclipse.jface.preference.StringFieldEditor;
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
import org.myau.shaya.ide.run.ShayaLastLaunch;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Preferences → ALG
 */
public class ShayaPreferencePage extends FieldEditorPreferencePage implements IWorkbenchPreferencePage {

	public ShayaPreferencePage() {
		super(GRID);
		setPreferenceStore(Activator.getDefault().getPreferenceStore());
		setDescription(
				"ALG IDE — SCHOOLALGOL (.alg).\n\n"
						+ "Toolchain home пустой = автопоиск dropins/"
						+ ShayaToolchain.DROPINS_FOLDER + "/.\n"
						+ "Один движок: .alg → interpreters/"
						+ ShayaToolchain.ENGINE_DIR + "/main.py.\n"
						+ "Extra args → tools/shaya-run.bat · Python пустой = PATH / py -3.\n"
						+ "Check on save: синтаксическая проверка (lex + parse).");
	}

	@Override
	public void init(IWorkbench workbench) {
	}

	@Override
	protected void createFieldEditors() {
		addField(new DirectoryFieldEditor(
				ShayaPreferenceConstants.TOOLCHAIN_HOME,
				"Toolchain home (" + ShayaToolchain.DROPINS_FOLDER + "):",
				getFieldEditorParent()));
		addField(new StringFieldEditor(
				ShayaPreferenceConstants.EXTRA_ARGS,
				"Extra args:",
				getFieldEditorParent()));
		addField(new FileFieldEditor(
				ShayaPreferenceConstants.PYTHON_EXECUTABLE,
				"Python (empty = PATH / py -3):",
				getFieldEditorParent()));
		IntegerFieldEditor indent = new IntegerFieldEditor(
				ShayaPreferenceConstants.INDENT_WIDTH,
				"Indent width (spaces, 2 or 4):",
				getFieldEditorParent());
		indent.setValidRange(2, 4);
		addField(indent);
		addField(new BooleanFieldEditor(
				ShayaPreferenceConstants.INSERT_SPACES,
				"Insert spaces for tabs (off = real tab character)",
				getFieldEditorParent()));
		addField(new BooleanFieldEditor(
				ShayaPreferenceConstants.CHECK_ON_SAVE,
				"Check on save (.alg)",
				getFieldEditorParent()));
		addField(new BooleanFieldEditor(
				ShayaPreferenceConstants.SHOW_WELCOME_ON_STARTUP,
				"Показать Welcome при следующем запуске Eclipse",
				getFieldEditorParent()));
	}

	@Override
	protected void contributeButtons(Composite parent) {
		super.contributeButtons(parent);
		((GridLayout) parent.getLayout()).numColumns += 2;

		Button validate = new Button(parent, SWT.PUSH);
		validate.setText("Validate…");
		validate.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
		validate.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				performApply();
				String status = ShayaToolchain.validateStatus();
				boolean ok = !status.contains("ОШИБКА");
				if (ok) {
					MessageDialog.openInformation(getShell(), "ALG Validate", status);
				} else {
					MessageDialog.openWarning(getShell(), "ALG Validate", status);
				}
			}
		});

		Button clear = new Button(parent, SWT.PUSH);
		clear.setText("Clear Recent");
		clear.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
		clear.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				ShayaLastLaunch.clearHistory();
				MessageDialog.openInformation(getShell(), "ALG",
						"Recent / Run Last history cleared.");
			}
		});
	}
}
