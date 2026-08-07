package org.myau.shaya.ide.launch;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.ILaunch;
import org.eclipse.debug.core.model.IProcess;
import org.eclipse.debug.ui.IDebugUIConstants;
import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.swt.widgets.Display;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.debug.model.ShayaDebugTarget;
import org.myau.shaya.ide.debug.model.ShayaSourceLocator;
import org.myau.shaya.ide.prefs.ShayaPreferenceConstants;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Eclipse step-debug launch for SCHOOLALGOL via {@code --debug-protocol} / SHAYDBG.
 */
public final class ShayaStepDebugLaunch {

	private ShayaStepDebugLaunch() {
	}

	public static void launch(IFile program, ILaunch launch) throws CoreException {
		File disk = program.getLocation() != null ? program.getLocation().toFile() : null;
		if (disk == null || !disk.isFile()) {
			abort("Source not on disk: " + program.getFullPath());
		}
		String engine = ShayaToolchain.engineIdFor(disk);
		if (!ShayaToolchain.supportsStepDebugUi(engine)) {
			abort(ShayaToolchain.stepDebugRefuseMessage(engine));
		}

		List<String> cmd = buildCommand(engine, disk, program);
		File cwd = ShayaToolchain.getEngineWorkDir(engine);
		if (cwd == null || !cwd.isDirectory()) {
			abort("Engine directory not found for " + engine);
		}

		ProcessBuilder pb = new ProcessBuilder(cmd);
		pb.directory(cwd);
		pb.redirectErrorStream(true);
		pb.environment().put("PYTHONIOENCODING", "utf-8");
		pb.environment().put("PYTHONUTF8", "1");
		pb.environment().put("PYTHONUNBUFFERED", "1");
		File home = ShayaToolchain.getToolchainHome();
		if (home != null) {
			pb.environment().put("SHAYA_TOOLCHAIN_HOME", home.getAbsolutePath());
		}

		Process process;
		try {
			process = pb.start();
		} catch (Exception e) {
			throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID,
					"Failed to start ALG step-debug: " + e.getMessage(), e));
		}

		Map<String, String> attrs = new HashMap<>();
		attrs.put(IProcess.ATTR_CMDLINE, String.join(" ", cmd));
		attrs.put(IProcess.ATTR_PROCESS_TYPE, "shaya-step-debug");
		IProcess iprocess = DebugPlugin.newProcess(launch, process, "ALG Step Debug: " + program.getName(),
				attrs);

		ShayaDebugTarget target = new ShayaDebugTarget(launch, iprocess, process, program);
		launch.addDebugTarget(target);
		launch.setSourceLocator(new ShayaSourceLocator(program));
		openDebugPerspective();
	}

	private static void openDebugPerspective() {
		Display display = Display.getDefault();
		if (display == null) {
			return;
		}
		display.asyncExec(() -> {
			try {
				if (!PlatformUI.isWorkbenchRunning()) {
					return;
				}
				IWorkbenchWindow win = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
				if (win != null) {
					PlatformUI.getWorkbench().showPerspective(IDebugUIConstants.ID_DEBUG_PERSPECTIVE, win);
				}
			} catch (Exception ignored) {
			}
		});
	}

	static List<String> buildCommand(String engine, File program, IFile workspaceFile)
			throws CoreException {
		String python = resolvePython();
		List<String> cmd = new ArrayList<>();
		cmd.add(python);
		cmd.add("-u");

		if (!ShayaToolchain.ENGINE_ALG.equals(engine)) {
			abort("Step Debug not wired for engine: " + engine);
		}
		File script = ShayaToolchain.getEngineEntryScript(ShayaToolchain.ENGINE_ALG);
		if (script == null || !script.isFile()) {
			abort("SCHOOLALGOL interpreter not found (main.py).");
		}
		cmd.add(script.getAbsolutePath());
		cmd.add(program.getAbsolutePath());
		cmd.add("--debug-protocol");
		for (Integer line : org.myau.shaya.ide.debug.ShayaBreakpoints.collectLines(workspaceFile)) {
			if (line != null && line.intValue() > 0) {
				cmd.add("--break");
				cmd.add(Integer.toString(line.intValue()));
			}
		}

		IPreferenceStore prefs = Activator.getDefault().getPreferenceStore();
		String extra = prefs.getString(ShayaPreferenceConstants.EXTRA_ARGS);
		if (extra != null && !extra.isBlank()) {
			for (String part : org.myau.shaya.ide.run.ShayaLauncher.splitQuotedArgsPublic(extra.trim())) {
				cmd.add(part);
			}
		}
		return cmd;
	}

	private static String resolvePython() throws CoreException {
		IPreferenceStore prefs = Activator.getDefault().getPreferenceStore();
		String configured = prefs.getString(ShayaPreferenceConstants.PYTHON_EXECUTABLE);
		if (configured != null && !configured.isBlank()) {
			File f = new File(configured.trim());
			if (f.isFile()) {
				return f.getAbsolutePath();
			}
		}
		String[] candidates = { "python", "py" };
		for (String c : candidates) {
			try {
				Process p = new ProcessBuilder(c, "-c", "import sys; print(sys.executable)")
						.redirectErrorStream(true).start();
				byte[] buf = p.getInputStream().readAllBytes();
				p.waitFor();
				String out = new String(buf, java.nio.charset.StandardCharsets.UTF_8).trim();
				if (!out.isEmpty() && new File(out).isFile()) {
					return out;
				}
			} catch (Exception ignored) {
			}
		}
		abort("Python 3 not found. Set Preferences → ALG → Python executable.");
		return null;
	}

	private static void abort(String message) throws CoreException {
		throw new CoreException(new Status(IStatus.ERROR, Activator.PLUGIN_ID, message));
	}
}
