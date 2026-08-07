package org.myau.shaya.ide.wizards;

import org.eclipse.core.resources.IContainer;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.IPath;
import org.eclipse.core.runtime.Path;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.WizardPage;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Combo;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Text;
import org.eclipse.ui.dialogs.ContainerSelectionDialog;

/** Page: container + stem + extension → engine. */
public class ShayaNewHelloWizardPage extends WizardPage {

	private final IStructuredSelection selection;
	private Text containerText;
	private Text stemText;
	private Combo dialectCombo;
	private final ShayaHelloBodies.Spec[] specs = ShayaHelloBodies.all();

	public ShayaNewHelloWizardPage(IStructuredSelection selection) {
		super("shayaHello");
		this.selection = selection;
		setTitle("ALG Hello");
		setDescription("Create a Hello.alg sample (RU or EN keywords) for SCHOOLALGOL.");
	}

	@Override
	public void createControl(Composite parent) {
		Composite root = new Composite(parent, SWT.NONE);
		root.setLayout(new GridLayout(3, false));

		new Label(root, SWT.NONE).setText("Folder:");
		containerText = new Text(root, SWT.BORDER);
		containerText.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		Button browse = new Button(root, SWT.PUSH);
		browse.setText("Browse…");
		browse.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				ContainerSelectionDialog dlg = new ContainerSelectionDialog(getShell(),
						ResourcesPlugin.getWorkspace().getRoot(), false, "Select folder");
				if (dlg.open() == ContainerSelectionDialog.OK && dlg.getResult() != null
						&& dlg.getResult().length > 0) {
					Object r = dlg.getResult()[0];
					if (r instanceof IPath) {
						containerText.setText(((IPath) r).toString());
					}
				}
				validate();
			}
		});

		new Label(root, SWT.NONE).setText("Name:");
		stemText = new Text(root, SWT.BORDER);
		stemText.setText("Hello");
		GridData stemGd = new GridData(SWT.FILL, SWT.CENTER, true, false);
		stemGd.horizontalSpan = 2;
		stemText.setLayoutData(stemGd);

		new Label(root, SWT.NONE).setText("Extension:");
		dialectCombo = new Combo(root, SWT.READ_ONLY);
		GridData comboGd = new GridData(SWT.FILL, SWT.CENTER, true, false);
		comboGd.horizontalSpan = 2;
		dialectCombo.setLayoutData(comboGd);
		for (ShayaHelloBodies.Spec s : specs) {
			dialectCombo.add(s.toString());
		}
		dialectCombo.select(0); // RU Hello.alg
		dialectCombo.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				ShayaHelloBodies.Spec s = getSpec();
				if (s != null && s.defaultStem != null && stemText != null) {
					String cur = stemText.getText().trim();
					// Update stem when switching dialect if still a default Hello* name
					if (cur.isEmpty() || cur.equals("Hello") || cur.equals("Hello_en")) {
						stemText.setText(s.defaultStem);
					}
				}
				validate();
			}
		});

		ModifyListener ml = new ModifyListener() {
			@Override
			public void modifyText(ModifyEvent e) {
				validate();
			}
		};
		containerText.addModifyListener(ml);
		stemText.addModifyListener(ml);

		initFromSelection();
		setControl(root);
		validate();
	}

	private void initFromSelection() {
		IContainer folder = null;
		if (selection != null && !selection.isEmpty()) {
			Object first = selection.getFirstElement();
			if (first instanceof IContainer) {
				folder = (IContainer) first;
			} else if (first instanceof IFile) {
				folder = ((IFile) first).getParent();
			} else if (first instanceof IResource) {
				IResource r = (IResource) first;
				folder = r instanceof IContainer ? (IContainer) r : r.getParent();
			}
		}
		if (folder == null) {
			IProject[] projects = ResourcesPlugin.getWorkspace().getRoot().getProjects();
			if (projects.length > 0) {
				folder = projects[0];
			}
		}
		if (folder != null) {
			containerText.setText(folder.getFullPath().toString());
		}
	}

	void validate() {
		setErrorMessage(null);
		setPageComplete(false);
		if (getTargetFolder() == null) {
			setErrorMessage("Select a project or folder");
			return;
		}
		String stem = getStem();
		if (stem == null || stem.isEmpty()) {
			setErrorMessage("Name required");
			return;
		}
		if (!stem.matches("[A-Za-zА-Яа-яЁё][A-Za-z0-9_А-Яа-яЁё]*")) {
			setErrorMessage("Use an identifier-like name");
			return;
		}
		ShayaHelloBodies.Spec spec = getSpec();
		if (spec == null) {
			setErrorMessage("Choose an extension");
			return;
		}
		IFile file = getTargetFolder().getFile(new Path(stem + "." + spec.ext));
		if (file.exists()) {
			setErrorMessage(file.getName() + " already exists");
			return;
		}
		setPageComplete(true);
	}

	IContainer getTargetFolder() {
		String path = containerText != null ? containerText.getText().trim() : "";
		if (path.isEmpty()) {
			return null;
		}
		IWorkspaceRoot root = ResourcesPlugin.getWorkspace().getRoot();
		IResource r = root.findMember(new Path(path));
		return r instanceof IContainer ? (IContainer) r : null;
	}

	String getStem() {
		return stemText != null ? stemText.getText().trim() : "";
	}

	ShayaHelloBodies.Spec getSpec() {
		int i = dialectCombo != null ? dialectCombo.getSelectionIndex() : -1;
		if (i < 0 || i >= specs.length) {
			return null;
		}
		return specs[i];
	}
}
