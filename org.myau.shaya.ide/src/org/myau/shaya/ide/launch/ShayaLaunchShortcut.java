package org.myau.shaya.ide.launch;

import java.io.File;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.ILaunchConfiguration;
import org.eclipse.debug.core.ILaunchConfigurationType;
import org.eclipse.debug.core.ILaunchConfigurationWorkingCopy;
import org.eclipse.debug.core.ILaunchManager;
import org.eclipse.debug.ui.DebugUITools;
import org.eclipse.debug.ui.ILaunchShortcut;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IFileEditorInput;
import org.eclipse.ui.PlatformUI;
import org.myau.shaya.ide.run.ShayaLastLaunch;
import org.myau.shaya.ide.run.ShayaLauncher;
import org.myau.shaya.ide.run.ShayaSourceResolver;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/** Run As / Debug As → ALG Application. */
public class ShayaLaunchShortcut implements ILaunchShortcut {

	@Override
	public void launch(ISelection selection, String mode) {
		IFile file = null;
		if (selection instanceof IStructuredSelection) {
			Object el = ((IStructuredSelection) selection).getFirstElement();
			if (el instanceof IFile) {
				file = (IFile) el;
			} else if (el instanceof IResource) {
				IResource r = (IResource) el;
				if (r.getType() == IResource.FILE) {
					file = (IFile) r;
				}
			}
		}
		launchFile(file, mode);
	}

	@Override
	public void launch(IEditorPart editor, String mode) {
		IFile file = null;
		if (editor != null) {
			IEditorInput input = editor.getEditorInput();
			if (input instanceof IFileEditorInput) {
				file = ((IFileEditorInput) input).getFile();
			}
			if (editor.isDirty()) {
				editor.doSave(null);
			}
		}
		launchFile(file, mode);
	}

	private void launchFile(IFile file, String mode) {
		if (file == null || !ShayaLaunchDelegate.isShayaSource(file)) {
			MessageDialog.openWarning(
					PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
					"ALG",
					"Open or select a ALG source (" + ShayaToolchain.extensionsHint() + ").");
			return;
		}
		File disk = file.getLocation() != null ? file.getLocation().toFile() : null;
		if (disk == null || !disk.isFile()) {
			MessageDialog.openWarning(
					PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
					"ALG",
					"Source not on disk: " + file.getFullPath());
			return;
		}
		ShayaSourceResolver.ResolvedSource src = new ShayaSourceResolver.ResolvedSource(disk, file);

		// Run As → same path as ALG → Run (console + markers + Recent).
		if (ILaunchManager.RUN_MODE.equals(mode)) {
			ShayaLastLaunch.remember(ShayaLastLaunch.Mode.RUN, src);
			ShayaLauncher.run(disk, file);
			return;
		}

		if (ILaunchManager.DEBUG_MODE.equals(mode)) {
			String engine = ShayaToolchain.engineIdForName(file.getName());
			boolean ok = engine != null && (ShayaToolchain.supportsStepDebugUi(engine)
					|| ShayaToolchain.supportsDebug(engine));
			if (!ok) {
				MessageDialog.openInformation(
						PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
						"ALG Debug",
						ShayaToolchain.debugRefuseMessage(engine));
				return;
			}
			ShayaLastLaunch.remember(ShayaLastLaunch.Mode.DEBUG, src);
		}
		try {
			ILaunchConfiguration config = findOrCreate(file);
			DebugUITools.launch(config, mode);
		} catch (CoreException e) {
			MessageDialog.openError(
					PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell(),
					"ALG",
					e.getMessage());
		}
	}

	public static ILaunchConfiguration findOrCreate(IFile file) throws CoreException {
		ILaunchManager manager = DebugPlugin.getDefault().getLaunchManager();
		ILaunchConfigurationType type = manager
				.getLaunchConfigurationType(ShayaLaunchConstants.LAUNCH_CONFIG_TYPE);
		String proj = file.getProject().getName();
		String path = file.getProjectRelativePath().toPortableString();
		for (ILaunchConfiguration existing : manager.getLaunchConfigurations(type)) {
			if (proj.equals(existing.getAttribute(ShayaLaunchConstants.ATTR_PROJECT, ""))
					&& path.equals(existing.getAttribute(ShayaLaunchConstants.ATTR_FILE, ""))) {
				return existing;
			}
		}
		String name = manager.generateLaunchConfigurationName("ALG: " + file.getName());
		ILaunchConfigurationWorkingCopy wc = type.newInstance(null, name);
		wc.setAttribute(ShayaLaunchConstants.ATTR_PROJECT, proj);
		wc.setAttribute(ShayaLaunchConstants.ATTR_FILE, path);
		wc.setMappedResources(new IResource[] { file });
		return wc.doSave();
	}
}
