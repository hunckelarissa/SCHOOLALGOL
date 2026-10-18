package org.myau.shaya.ide.run;

import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.swt.widgets.Display;
import org.eclipse.ui.console.IOConsole;
import org.eclipse.ui.console.IOConsoleOutputStream;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.markers.ShayaMarkers;
import org.myau.shaya.ide.prefs.ShayaPreferenceConstants;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Invokes tools/shaya-run.bat for Run / Check.
 * Works for workspace files and File→Open (external) paths.
 */
public final class ShayaLauncher {

	private ShayaLauncher() {
	}

	public static void run(File program, IFile workspaceFile) {
		launch(program, workspaceFile, "--run", true);
	}

	public static void check(File program, IFile workspaceFile) {
		String engine = ShayaToolchain.engineIdFor(program);
		if (engine != null && !ShayaToolchain.supportsCheck(engine)) {
			ShayaConsole.showError(
					"Check не поддерживается для " + ShayaToolchain.engineDisplayName(engine)
							+ ".\nДля .alg используйте Run.");
			return;
		}
		launch(program, workspaceFile, "--check", true);
	}

	public static void debug(File program, IFile workspaceFile) {
		launch(program, workspaceFile, "--debug", true);
	}

	/**
	 * Synchronous --check for build-on-save style flows (no console clear, markers applied).
	 */
	public static int checkSync(IFile programFile, IProgressMonitor monitor) {
		File disk = local(programFile);
		if (disk == null) {
			return 1;
		}
		File wrapper = ShayaToolchain.getRunWrapper();
		if (wrapper == null) {
			return 1;
		}
		List<String> cmd = buildCommand(wrapper, disk, "--check");
		try {
			Result r = runProcess(cmd, disk.getParentFile(), monitor, null);
			if (programFile.exists()) {
				ShayaMarkers.applyFromProcessOutput(programFile, r.output, r.exitCode);
			}
			return r.exitCode;
		} catch (Exception e) {
			try {
				ShayaMarkers.applyFromProcessOutput(programFile, e.getMessage(), 1);
			} catch (Exception ignored) {
			}
			return 1;
		}
	}

	private static File local(IFile programFile) {
		if (programFile.getLocation() == null) {
			ShayaConsole.showError("Нет локального пути для " + programFile.getFullPath());
			return null;
		}
		return programFile.getLocation().toFile();
	}

	private static void launch(File program, IFile workspaceFile, String mode, boolean clearConsole) {
		File wrapper = ShayaToolchain.getRunWrapper();
		if (wrapper == null) {
			ShayaConsole.showError(
					"Toolchain ALG не найден.\n\n"
							+ "1. Запустите .\\install_dropins.ps1 (копирует tools\\shaya-run.bat и *.py)\n"
							+ "2. Preferences → ALG → Toolchain home = dropins/"
							+ ShayaToolchain.DROPINS_FOLDER + "\n"
							+ "3. Нажмите Validate…");
			return;
		}
		if (program == null || !program.isFile()) {
			ShayaConsole.showError("Исходный файл не найден на диске.");
			return;
		}

		String engineId = ShayaToolchain.engineIdFor(program);
		if (engineId == null) {
			ShayaConsole.showError(
					"Неизвестное расширение ALG: " + program.getName() + "\n"
							+ ShayaToolchain.enginesHint()
							+ "\nОткройте файл .alg.");
			return;
		}

		List<String> cmd = buildCommand(wrapper, program, mode);
		File workDir = program.getParentFile();
		IOConsole console = ShayaConsole.getConsole();
		if (clearConsole) {
			console.clearConsole();
		}
		IOConsoleOutputStream out;
		try {
			out = console.newOutputStream();
			out.setEncoding(StandardCharsets.UTF_8.name());
		} catch (Exception e) {
			ShayaConsole.showError("Консоль: " + e.getMessage());
			return;
		}

		writeLine(out, ">>> " + String.join(" ", cmd));
		writeLine(out, "cwd: " + workDir.getAbsolutePath());
		writeLine(out, "engine: " + ShayaToolchain.engineDisplayName(engineId));
		writeLine(out, "toolchain: " + String.valueOf(ShayaToolchain.getToolchainHome()));
		writeLine(out, "---");

		final IFile markerFile = workspaceFile;
		String jobName;
		if ("--check".equals(mode)) {
			jobName = "Check ALG: " + program.getName();
		} else if ("--debug".equals(mode)) {
			jobName = "Debug ALG: " + program.getName();
		} else {
			jobName = "Run ALG: " + program.getName();
		}
		Job job = new Job(jobName) {
			@Override
			protected IStatus run(IProgressMonitor monitor) {
				try {
					Result r = runProcess(cmd, workDir, monitor, out);
					Display.getDefault().asyncExec(() -> {
						writeLine(out, "---");
						writeLine(out, "exit code: " + r.exitCode);
						if (markerFile != null && markerFile.exists()) {
							try {
								ShayaMarkers.applyFromProcessOutput(markerFile, r.output, r.exitCode);
							} catch (Exception e) {
								writeLine(out, "markers: " + e.getMessage());
							}
						}
					});
					return Status.OK_STATUS;
				} catch (Exception e) {
					final String msg = e.getMessage();
					Display.getDefault().asyncExec(() -> writeLine(out, "Ошибка запуска: " + msg));
					return new Status(IStatus.ERROR, Activator.PLUGIN_ID, e.getMessage(), e);
				}
			}
		};
		job.setUser(true);
		job.schedule();
	}

	/** Public for Launch Framework (Run As / Debug As). */
	public static List<String> buildLaunchCommand(File program, String mode) {
		File wrapper = ShayaToolchain.getRunWrapper();
		if (wrapper == null || program == null) {
			return null;
		}
		return buildCommand(wrapper, program, mode);
	}

	private static List<String> buildCommand(File wrapper, File program, String mode) {
		IPreferenceStore prefs = Activator.getDefault().getPreferenceStore();
		String extra = prefs.getString(ShayaPreferenceConstants.EXTRA_ARGS);
		List<String> cmd = new ArrayList<>();
		cmd.add("cmd.exe");
		cmd.add("/c");
		cmd.add(wrapper.getAbsolutePath());
		cmd.add(program.getAbsolutePath());
		cmd.add(mode);
		if (extra != null && !extra.isBlank()) {
			for (String part : splitQuotedArgs(extra.trim())) {
				cmd.add(part);
			}
		}
		return cmd;
	}

	/**
	 * Split Extra args with Windows-friendly quoting: {@code "a b"} stays one token.
	 * Backslash only escapes the next character inside quotes.
	 */
	/** Public for step-debug launch command assembly. */
	public static List<String> splitQuotedArgsPublic(String raw) {
		return splitQuotedArgs(raw);
	}

	static List<String> splitQuotedArgs(String raw) {
		List<String> out = new ArrayList<>();
		if (raw == null || raw.isEmpty()) {
			return out;
		}
		StringBuilder cur = new StringBuilder();
		boolean inQuotes = false;
		for (int i = 0; i < raw.length(); i++) {
			char c = raw.charAt(i);
			if (c == '"' ) {
				inQuotes = !inQuotes;
				continue;
			}
			if (!inQuotes && Character.isWhitespace(c)) {
				if (cur.length() > 0) {
					out.add(cur.toString());
					cur.setLength(0);
				}
				continue;
			}
			if (c == '\\' && i + 1 < raw.length()) {
				cur.append(raw.charAt(++i));
				continue;
			}
			cur.append(c);
		}
		if (cur.length() > 0) {
			out.add(cur.toString());
		}
		return out;
	}

	private static Result runProcess(List<String> cmd, File workDir, IProgressMonitor monitor,
			IOConsoleOutputStream out) throws Exception {
		if (monitor == null) {
			monitor = new NullProgressMonitor();
		}
		ProcessBuilder pb = new ProcessBuilder(cmd);
		pb.directory(workDir);
		pb.redirectErrorStream(true);
		File home = ShayaToolchain.getToolchainHome();
		if (home != null) {
			pb.environment().put("SHAYA_TOOLCHAIN_HOME", home.getAbsolutePath());
		}
		IPreferenceStore prefs = Activator.getDefault().getPreferenceStore();
		String py = prefs.getString(ShayaPreferenceConstants.PYTHON_EXECUTABLE);
		if (py != null && !py.isBlank()) {
			pb.environment().put("SHAYA_PYTHON", py.trim());
		}
		Process process = pb.start();
		StringBuilder capture = new StringBuilder();
		byte[] buf = new byte[1024];
		try (InputStream in = process.getInputStream()) {
			int n;
			while ((n = in.read(buf)) >= 0) {
				if (monitor.isCanceled()) {
					process.destroy();
					break;
				}
				String chunk = new String(buf, 0, n, StandardCharsets.UTF_8);
				capture.append(chunk);
				if (out != null) {
					try {
						out.write(chunk.getBytes(StandardCharsets.UTF_8));
						out.flush();
					} catch (Exception ignored) {
					}
				}
			}
		}
		int code = process.waitFor();
		if (process.isAlive()) {
			process.destroy();
		}
		return new Result(code, capture.toString());
	}

	private static void writeLine(IOConsoleOutputStream out, String line) {
		try {
			out.write((line + "\n").getBytes(StandardCharsets.UTF_8));
			out.flush();
		} catch (Exception ignored) {
		}
	}

	private static final class Result {
		final int exitCode;
		final String output;

		Result(int exitCode, String output) {
			this.exitCode = exitCode;
			this.output = output;
		}
	}
}
