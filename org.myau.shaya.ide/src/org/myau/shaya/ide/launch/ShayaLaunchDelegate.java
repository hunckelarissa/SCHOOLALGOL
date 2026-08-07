package org.myau.shaya.ide.launch;

import java.io.File;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.debug.core.ILaunch;
import org.eclipse.debug.core.ILaunchConfiguration;
import org.eclipse.debug.core.ILaunchManager;
import org.eclipse.debug.core.model.ILaunchConfigurationDelegate;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.run.ShayaLastLaunch;
import org.myau.shaya.ide.run.ShayaLauncher;
import org.myau.shaya.ide.run.ShayaSourceResolver;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Run / Debug launch.
 * <ul>
 * <li>RUN — console via wrapper ({@link ShayaLauncher#run})</li>
 * <li>DEBUG + step-protocol engine — Eclipse Debug Framework ({@link ShayaStepDebugLaunch})</li>
 * <li>DEBUG + CLI-only engine — console CLI debug ({@link ShayaLauncher#debug}), unchanged</li>
 * </ul>
 */
public class ShayaLaunchDelegate implements ILaunchConfigurationDelegate {

	@Override
	public void launch(ILaunchConfiguration configuration, String mode, ILaunch launch,
			IProgressMonitor monitor) throws CoreException {
		IFile program = resolveProgram(configuration);
		File disk = program.getLocation() != null ? program.getLocation().toFile() : null;
		if (disk == null || !disk.isFile()) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"Source not on disk: " + program.getFullPath()));
		}
		if (ShayaToolchain.getRunWrapper() == null && !ILaunchManager.DEBUG_MODE.equals(mode)) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"ALG toolchain not found (dropins/schoolalgol-shaya or Preferences → ALG)."));
		}

		String engine = ShayaToolchain.engineIdFor(disk);
		if (engine == null) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"Unknown ALG extension: " + program.getName()));
		}

		boolean debug = ILaunchManager.DEBUG_MODE.equals(mode);
		ShayaSourceResolver.ResolvedSource src = new ShayaSourceResolver.ResolvedSource(disk, program);

		if (!debug) {
			if (ShayaToolchain.getRunWrapper() == null) {
				throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
						"ALG toolchain not found (dropins/schoolalgol-shaya or Preferences → ALG)."));
			}
			ShayaLastLaunch.remember(ShayaLastLaunch.Mode.RUN, src);
			ShayaLauncher.run(disk, program);
			return;
		}

		// DEBUG mode: prefer step-protocol when available; else CLI debug.
		if (ShayaToolchain.supportsStepDebugUi(engine)) {
			ShayaLastLaunch.remember(ShayaLastLaunch.Mode.DEBUG, src);
			ShayaStepDebugLaunch.launch(program, launch);
			return;
		}
		if (ShayaToolchain.supportsDebug(engine)) {
			if (ShayaToolchain.getRunWrapper() == null) {
				throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
						"ALG toolchain not found (dropins/schoolalgol-shaya or Preferences → ALG)."));
			}
			ShayaLastLaunch.remember(ShayaLastLaunch.Mode.DEBUG, src);
			ShayaLauncher.debug(disk, program);
			return;
		}
		throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
				ShayaToolchain.debugRefuseMessage(engine)));
	}

	static IFile resolveProgram(ILaunchConfiguration configuration) throws CoreException {
		String project = configuration.getAttribute(ShayaLaunchConstants.ATTR_PROJECT, "");
		String filePath = configuration.getAttribute(ShayaLaunchConstants.ATTR_FILE, "");
		if (project.isEmpty() || filePath.isEmpty()) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"Launch config missing project or file."));
		}
		org.eclipse.core.resources.IProject proj = org.eclipse.core.resources.ResourcesPlugin.getWorkspace()
				.getRoot().getProject(project);
		if (!proj.exists()) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"Project not found: " + project));
		}
		org.eclipse.core.runtime.IPath path = org.eclipse.core.runtime.Path.fromPortableString(filePath);
		IFile file = proj.getFile(path);
		if (!file.exists()) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"File not found: " + project + "/" + filePath));
		}
		return file;
	}

	static boolean isShayaSource(IFile file) {
		return file != null && ShayaToolchain.isShayaSource(file.getName());
	}
}
