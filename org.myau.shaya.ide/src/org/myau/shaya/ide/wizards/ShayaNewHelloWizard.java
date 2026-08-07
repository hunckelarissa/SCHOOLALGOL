package org.myau.shaya.ide.wizards;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

import org.eclipse.core.resources.IContainer;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.Path;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.ide.IDE;

/**
 * File → New → ALG → ALG Hello — pick extension → engine, create sample file.
 */
public class ShayaNewHelloWizard extends Wizard implements INewWizard {

	private IWorkbench workbench;
	private IStructuredSelection selection;
	private ShayaNewHelloWizardPage page;

	@Override
	public void init(IWorkbench workbench, IStructuredSelection selection) {
		this.workbench = workbench;
		this.selection = selection;
		setWindowTitle("New ALG Hello");
		setNeedsProgressMonitor(false);
	}

	@Override
	public void addPages() {
		page = new ShayaNewHelloWizardPage(selection);
		addPage(page);
	}

	@Override
	public boolean performFinish() {
		IContainer folder = page.getTargetFolder();
		ShayaHelloBodies.Spec spec = page.getSpec();
		String stem = page.getStem();
		if (folder == null || spec == null || stem == null || stem.isEmpty()) {
			return false;
		}
		String fileName = stem + "." + spec.ext;
		IFile file = folder.getFile(new Path(fileName));
		if (file.exists()) {
			page.setErrorMessage(fileName + " already exists.");
			return false;
		}
		try {
			file.create(new ByteArrayInputStream(spec.body.getBytes(StandardCharsets.UTF_8)), true, null);
			ShayaWizardSupport.ensureNature(file);
			folder.refreshLocal(IResource.DEPTH_ONE, null);
			IDE.openEditor(workbench.getActiveWorkbenchWindow().getActivePage(), file);
			return true;
		} catch (Exception e) {
			page.setErrorMessage(e.getMessage());
			return false;
		}
	}
}
