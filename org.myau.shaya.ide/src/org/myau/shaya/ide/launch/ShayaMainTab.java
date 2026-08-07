package org.myau.shaya.ide.launch;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Path;
import org.eclipse.core.runtime.Status;
import org.eclipse.debug.core.ILaunchConfiguration;
import org.eclipse.debug.core.ILaunchConfigurationWorkingCopy;
import org.eclipse.debug.ui.AbstractLaunchConfigurationTab;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Text;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;
import org.eclipse.ui.dialogs.ElementTreeSelectionDialog;
import org.eclipse.ui.model.WorkbenchContentProvider;
import org.eclipse.ui.model.WorkbenchLabelProvider;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/** Main tab: project + source file with Browse and extension validation. */
public class ShayaMainTab extends AbstractLaunchConfigurationTab {

	private Text projectText;
	private Text fileText;

	@Override
	public void createControl(Composite parent) {
		Composite root = new Composite(parent, SWT.NONE);
		setControl(root);
		root.setLayout(new GridLayout(3, false));

		new Label(root, SWT.NONE).setText("Project:");
		projectText = new Text(root, SWT.BORDER);
		projectText.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		Button browseProj = new Button(root, SWT.PUSH);
		browseProj.setText("Browse…");
		browseProj.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				browseProject();
			}
		});

		new Label(root, SWT.NONE).setText("File:");
		fileText = new Text(root, SWT.BORDER);
		fileText.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		Button browseFile = new Button(root, SWT.PUSH);
		browseFile.setText("Browse…");
		browseFile.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {
				browseFile();
			}
		});

		ModifyListener ml = new ModifyListener() {
			@Override
			public void modifyText(ModifyEvent e) {
				updateLaunchConfigurationDialog();
			}
		};
		projectText.addModifyListener(ml);
		fileText.addModifyListener(ml);
	}

	private void browseProject() {
		IProject[] projects = ResourcesPlugin.getWorkspace().getRoot().getProjects();
		ElementListSelectionDialog dlg = new ElementListSelectionDialog(getShell(), new LabelProvider() {
			@Override
			public String getText(Object element) {
				return element instanceof IProject ? ((IProject) element).getName() : super.getText(element);
			}
		});
		dlg.setTitle("ALG Project");
		dlg.setMessage("Select a workspace project:");
		dlg.setElements(projects);
		if (dlg.open() == Window.OK && dlg.getFirstResult() instanceof IProject) {
			projectText.setText(((IProject) dlg.getFirstResult()).getName());
		}
	}

	private void browseFile() {
		String projName = projectText.getText().trim();
		IProject project = projName.isEmpty() ? null
				: ResourcesPlugin.getWorkspace().getRoot().getProject(projName);
		ElementTreeSelectionDialog dlg = new ElementTreeSelectionDialog(getShell(),
				new WorkbenchLabelProvider(), new WorkbenchContentProvider());
		dlg.setTitle("ALG Source");
		dlg.setMessage("Select a ALG source file:");
		dlg.setInput(project != null && project.exists()
				? project
				: ResourcesPlugin.getWorkspace().getRoot());
		dlg.setAllowMultiple(false);
		dlg.setValidator(selection -> {
			if (selection == null || selection.length != 1 || !(selection[0] instanceof IFile)) {
				return new Status(IStatus.ERROR, "org.myau.shaya.ide", "Select a file");
			}
			IFile f = (IFile) selection[0];
			if (!ShayaToolchain.isShayaSource(f.getName())) {
				return new Status(IStatus.ERROR, "org.myau.shaya.ide",
						"Not a ALG extension (" + ShayaToolchain.extensionsHint() + ")");
			}
			return Status.OK_STATUS;
		});
		if (dlg.open() == Window.OK && dlg.getFirstResult() instanceof IFile) {
			IFile f = (IFile) dlg.getFirstResult();
			projectText.setText(f.getProject().getName());
			fileText.setText(f.getProjectRelativePath().toPortableString());
		}
	}

	@Override
	public void setDefaults(ILaunchConfigurationWorkingCopy configuration) {
		configuration.setAttribute(ShayaLaunchConstants.ATTR_PROJECT, "");
		configuration.setAttribute(ShayaLaunchConstants.ATTR_FILE, "");
	}

	@Override
	public void initializeFrom(ILaunchConfiguration configuration) {
		try {
			projectText.setText(configuration.getAttribute(ShayaLaunchConstants.ATTR_PROJECT, ""));
			fileText.setText(configuration.getAttribute(ShayaLaunchConstants.ATTR_FILE, ""));
		} catch (CoreException e) {
			projectText.setText("");
			fileText.setText("");
		}
	}

	@Override
	public void performApply(ILaunchConfigurationWorkingCopy configuration) {
		String project = projectText.getText().trim();
		String file = fileText.getText().trim();
		configuration.setAttribute(ShayaLaunchConstants.ATTR_PROJECT, project);
		configuration.setAttribute(ShayaLaunchConstants.ATTR_FILE, file);
		IFile f = ResourcesPlugin.getWorkspace().getRoot().getFile(new Path(project + "/" + file));
		if (f.exists()) {
			configuration.setMappedResources(new IResource[] { f });
		}
	}

	@Override
	public String getName() {
		return "ALG";
	}

	@Override
	public boolean isValid(ILaunchConfiguration launchConfig) {
		setErrorMessage(null);
		String project = projectText.getText().trim();
		String file = fileText.getText().trim();
		if (project.isEmpty() || file.isEmpty()) {
			setErrorMessage("Specify project and source file");
			return false;
		}
		IProject p = ResourcesPlugin.getWorkspace().getRoot().getProject(project);
		if (!p.exists()) {
			setErrorMessage("Project not found: " + project);
			return false;
		}
		IFile f = p.getFile(new Path(file));
		if (!f.exists()) {
			setErrorMessage("File not found: " + file);
			return false;
		}
		if (!ShayaToolchain.isShayaSource(f.getName())) {
			setErrorMessage("Not a ALG extension: " + f.getName());
			return false;
		}
		return true;
	}
}
