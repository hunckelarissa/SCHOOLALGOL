package org.myau.shaya.ide.wizards;

import java.io.ByteArrayInputStream;
import java.lang.reflect.InvocationTargetException;
import java.net.URI;
import java.nio.charset.StandardCharsets;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IProjectDescription;
import org.eclipse.core.resources.IWorkspaceRunnable;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.dialogs.WizardNewProjectCreationPage;
import org.eclipse.ui.ide.IDE;
import org.myau.shaya.ide.nature.ShayaNatureSupport;

/**
 * File → New → Project → ALG Project (nature + Hello samples for all map extensions).
 */
public class ShayaNewProjectWizard extends Wizard implements INewWizard {

	private IWorkbench workbench;
	private WizardNewProjectCreationPage page;

	@Override
	public void init(IWorkbench workbench, IStructuredSelection selection) {
		this.workbench = workbench;
		setWindowTitle("New ALG Project");
		setNeedsProgressMonitor(true);
	}

	@Override
	public void addPages() {
		page = new WizardNewProjectCreationPage("shayaProject");
		page.setTitle("ALG Project");
		page.setDescription(
				"Creates an ALG project with Hello.alg (RU) and Hello_en.alg (EN) for SCHOOLALGOL.");
		addPage(page);
	}

	@Override
	public boolean performFinish() {
		final IProject project = page.getProjectHandle();
		final URI location = page.getLocationURI();
		try {
			getContainer().run(true, true, monitor -> {
				try {
					ResourcesPlugin.getWorkspace().run((IWorkspaceRunnable) mon -> {
						createProject(project, location, mon);
					}, monitor);
				} catch (CoreException e) {
					throw new InvocationTargetException(e);
				}
			});
		} catch (InterruptedException e) {
			Thread.currentThread().interrupt();
			page.setErrorMessage("Cancelled.");
			return false;
		} catch (InvocationTargetException e) {
			Throwable cause = e.getCause() != null ? e.getCause() : e;
			String msg = cause.getMessage() != null ? cause.getMessage() : cause.toString();
			page.setErrorMessage(msg);
			if (project.exists()) {
				MessageDialog.openWarning(getShell(), "ALG Project",
						"Project was created but setup is incomplete:\n\n" + msg
								+ "\n\nYou can delete the project and try again,"
								+ " or finish Hello samples manually.");
			} else {
				MessageDialog.openError(getShell(), "ALG Project", msg);
			}
			return false;
		}

		try {
			IFile open = project.getFile("Hello.alg");
			if (open.exists() && workbench.getActiveWorkbenchWindow() != null) {
				IDE.openEditor(workbench.getActiveWorkbenchWindow().getActivePage(), open);
			}
		} catch (Exception ignored) {
		}
		return true;
	}

	private static void createProject(IProject project, URI location, IProgressMonitor monitor)
			throws CoreException {
		IProjectDescription desc = project.getWorkspace().newProjectDescription(project.getName());
		if (location != null) {
			desc.setLocationURI(location);
		}
		project.create(desc, monitor);
		project.open(monitor);
		ShayaNatureSupport.addNature(project);

		ShayaHelloBodies.Spec[] specs = ShayaHelloBodies.projectDefaults();
		monitor.beginTask("ALG samples", specs.length + 1);
		for (ShayaHelloBodies.Spec spec : specs) {
			String stem = spec.defaultStem != null ? spec.defaultStem : "Hello";
			create(project, stem + "." + spec.ext, spec.body);
			monitor.worked(1);
		}

		create(project, "README-ALG.txt", ""
				+ "ALG IDE / SCHOOLALGOL\n"
				+ "=====================\n"
				+ "\n"
				+ "Extension .alg → SCHOOLALGOL interpreter (main.py).\n"
				+ "Keywords: Russian (алг/нач/кон) and English (proc/begin/end).\n"
				+ "\n"
				+ "Open Hello.alg (RU) or Hello_en.alg (EN) → ALG → Run / Check.\n"
				+ "Need: Python 3 on PATH (or Preferences → ALG → Python).\n"
				+ "Toolchain: dropins/schoolalgol-shaya/\n"
				+ "\n"
				+ "Расширение .alg → интерпретатор SCHOOLALGOL.\n"
				+ "Ключевые слова: русский и английский синонимы.\n");
		monitor.worked(1);
		monitor.done();
	}

	private static void create(IProject project, String name, String content) throws CoreException {
		IFile file = project.getFile(name);
		if (!file.exists()) {
			file.create(new ByteArrayInputStream(content.getBytes(StandardCharsets.UTF_8)), true, null);
		}
	}
}
