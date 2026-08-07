package org.myau.shaya.ide.run;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.Path;
import org.eclipse.jface.dialogs.IDialogSettings;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Remembers last Run / Check / Debug and a short Recent history (persisted).
 */
public final class ShayaLastLaunch {

	public enum Mode {
		RUN, CHECK, DEBUG
	}

	public static final class Entry {
		public final Mode mode;
		public final String diskPath;
		public final String workspacePath;

		public Entry(Mode mode, String diskPath, String workspacePath) {
			this.mode = mode;
			this.diskPath = diskPath;
			this.workspacePath = workspacePath;
		}

		public String label() {
			String m = mode == Mode.RUN ? "Run" : (mode == Mode.CHECK ? "Check" : "Debug");
			String name = new File(diskPath).getName();
			String engId = ShayaToolchain.engineIdForName(name);
			String eng = engId != null ? ShayaToolchain.engineDisplayName(engId) : "?";
			return m + " · " + name + " · " + eng;
		}
	}

	private static final String SECTION = "lastLaunch";
	private static final String KEY_MODE = "mode";
	private static final String KEY_DISK = "disk";
	private static final String KEY_WS = "workspace";
	private static final String KEY_HIST = "history";
	private static final int MAX_RECENT = 8;

	private static volatile Mode mode;
	private static volatile String diskPath;
	private static volatile String workspacePath;
	private static final List<Entry> history = new ArrayList<>();

	private ShayaLastLaunch() {
	}

	public static synchronized void load() {
		try {
			IDialogSettings s = section(false);
			if (s == null) {
				return;
			}
			String m = s.get(KEY_MODE);
			String d = s.get(KEY_DISK);
			String w = s.get(KEY_WS);
			if (m != null && d != null && !d.isBlank()) {
				mode = Mode.valueOf(m);
				diskPath = d;
				workspacePath = w;
			}
			history.clear();
			String[] hist = s.getArray(KEY_HIST);
			if (hist != null) {
				for (String line : hist) {
					Entry e = parseHist(line);
					if (e != null) {
						history.add(e);
					}
				}
			}
			// Seed Recent from last launch if history file was empty / older format
			if (history.isEmpty() && mode != null && diskPath != null && !diskPath.isBlank()) {
				history.add(new Entry(mode, diskPath, workspacePath));
			}
		} catch (Exception ignored) {
		}
	}

	public static synchronized void save() {
		try {
			IDialogSettings s = section(true);
			if (s == null) {
				return;
			}
			if (mode != null && diskPath != null) {
				s.put(KEY_MODE, mode.name());
				s.put(KEY_DISK, diskPath);
				s.put(KEY_WS, workspacePath != null ? workspacePath : "");
			}
			String[] arr = new String[history.size()];
			for (int i = 0; i < history.size(); i++) {
				Entry e = history.get(i);
				arr[i] = e.mode.name() + "|" + e.diskPath + "|"
						+ (e.workspacePath != null ? e.workspacePath : "");
			}
			s.put(KEY_HIST, arr);
			Activator act = Activator.getDefault();
			if (act != null) {
				act.persistDialogSettings();
			}
		} catch (Exception ignored) {
		}
	}

	public static synchronized void clearHistory() {
		history.clear();
		mode = null;
		diskPath = null;
		workspacePath = null;
		save();
	}

	public static synchronized void remember(Mode m, ShayaSourceResolver.ResolvedSource src) {
		if (m == null || src == null || src.file == null) {
			return;
		}
		mode = m;
		diskPath = src.file.getAbsolutePath();
		workspacePath = src.workspaceFile != null ? src.workspaceFile.getFullPath().toString() : null;
		Entry e = new Entry(m, diskPath, workspacePath);
		history.removeIf(h -> diskPath.equalsIgnoreCase(h.diskPath));
		history.add(0, e);
		while (history.size() > MAX_RECENT) {
			history.remove(history.size() - 1);
		}
		save();
	}

	public static boolean hasLast() {
		return mode != null && diskPath != null && !diskPath.isBlank();
	}

	public static Mode lastMode() {
		return mode;
	}

	public static ShayaSourceResolver.ResolvedSource lastSource() {
		return toSource(mode, diskPath, workspacePath);
	}

	public static synchronized List<Entry> recent() {
		return Collections.unmodifiableList(new ArrayList<>(history));
	}

	public static ShayaSourceResolver.ResolvedSource toSource(Entry e) {
		if (e == null) {
			return null;
		}
		return toSource(e.mode, e.diskPath, e.workspacePath);
	}

	public static String describe() {
		if (!hasLast()) {
			return "(none)";
		}
		String m = mode == Mode.RUN ? "Run" : (mode == Mode.CHECK ? "Check" : "Debug");
		return m + " · " + new File(diskPath).getName();
	}

	private static ShayaSourceResolver.ResolvedSource toSource(Mode m, String disk, String wsPath) {
		if (m == null || disk == null || disk.isBlank()) {
			return null;
		}
		File f = new File(disk);
		if (!f.isFile()) {
			return null;
		}
		IFile ws = null;
		if (wsPath != null && !wsPath.isBlank()) {
			IWorkspaceRoot root = ResourcesPlugin.getWorkspace().getRoot();
			ws = root.getFile(new Path(wsPath));
			if (ws != null && !ws.exists()) {
				ws = null;
			}
		}
		return new ShayaSourceResolver.ResolvedSource(f, ws);
	}

	private static Entry parseHist(String line) {
		if (line == null || line.isBlank()) {
			return null;
		}
		String[] p = line.split("\\|", 3);
		if (p.length < 2) {
			return null;
		}
		try {
			Mode m = Mode.valueOf(p[0]);
			String d = p[1];
			String w = p.length > 2 && !p[2].isBlank() ? p[2] : null;
			if (d == null || d.isBlank()) {
				return null;
			}
			return new Entry(m, d, w);
		} catch (Exception e) {
			return null;
		}
	}

	private static IDialogSettings section(boolean create) {
		Activator act = Activator.getDefault();
		if (act == null) {
			return null;
		}
		IDialogSettings root = act.getDialogSettings();
		IDialogSettings s = root.getSection(SECTION);
		if (s == null && create) {
			s = root.addNewSection(SECTION);
		}
		return s;
	}
}
