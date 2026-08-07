package org.myau.shaya.ide.run;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.core.filesystem.EFS;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceProxy;
import org.eclipse.core.resources.IResourceProxyVisitor;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IPath;
import org.eclipse.core.runtime.Path;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.console.IHyperlink;
import org.eclipse.ui.console.IPatternMatchListenerDelegate;
import org.eclipse.ui.console.PatternMatchEvent;
import org.eclipse.ui.console.TextConsole;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.texteditor.ITextEditor;

/**
 * Clickable file:line and (строка N) links in the ALG console.
 */
public class ShayaConsoleHyperlinkMatcher implements IPatternMatchListenerDelegate {

	private static final String EXT = "alg";

	/**
	 * Quoted paths (spaces OK) or bare paths, then :line.
	 * Group 1 = quoted path, group 2 = bare path, group 3 = line.
	 */
	public static final String REGEX = "(?:\\\"((?:[A-Za-z]:)?[^\"]+\\." + EXT
			+ ")\\\"|((?:[A-Za-z]:)?[^\\s\\\"']+\\." + EXT + "))(?:\\s*:\\s*|:)(\\d+)";

	/** line N / строка N — jump into last-run source. */
	public static final String LINE_REGEX = "(?i)(?:line|строка)\\s*(\\d+)";

	private static final Pattern EXTRACT = Pattern.compile(REGEX, Pattern.CASE_INSENSITIVE);
	private static final Pattern LINE_EXTRACT = Pattern.compile(LINE_REGEX);

	private TextConsole console;
	private final boolean lineOnly;

	public ShayaConsoleHyperlinkMatcher() {
		this(false);
	}

	public ShayaConsoleHyperlinkMatcher(boolean lineOnly) {
		this.lineOnly = lineOnly;
	}

	@Override
	public void connect(TextConsole console) {
		this.console = console;
	}

	@Override
	public void disconnect() {
		this.console = null;
	}

	@Override
	public void matchFound(PatternMatchEvent event) {
		if (console == null) {
			return;
		}
		try {
			int offset = event.getOffset();
			int length = event.getLength();
			String text = console.getDocument().get(offset, length);
			if (lineOnly) {
				Matcher m = LINE_EXTRACT.matcher(text);
				if (!m.find()) {
					return;
				}
				int line = Integer.parseInt(m.group(1));
				console.addHyperlink(new LastSourceLineLink(line), offset + m.start(1), m.end(1) - m.start(1));
				return;
			}
			Matcher m = EXTRACT.matcher(text);
			if (!m.find()) {
				return;
			}
			String path = m.group(1) != null ? m.group(1) : m.group(2);
			int line = Integer.parseInt(m.group(3));
			int linkStart = m.group(1) != null ? m.start(1) : m.start(2);
			console.addHyperlink(new FileLineLink(path, line), offset + linkStart, m.end(3) - linkStart);
		} catch (BadLocationException | NumberFormatException ignored) {
		}
	}

	private static void openAtLine(IFile file, File disk, int line) {
		try {
			IWorkbenchPage page = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage();
			IEditorPart editor;
			if (file != null && file.exists()) {
				editor = IDE.openEditor(page, file, true);
			} else if (disk != null && disk.isFile()) {
				editor = IDE.openEditorOnFileStore(page, EFS.getLocalFileSystem().fromLocalFile(disk));
			} else {
				return;
			}
			if (editor instanceof ITextEditor && line > 0) {
				ITextEditor te = (ITextEditor) editor;
				IDocument doc = te.getDocumentProvider().getDocument(editor.getEditorInput());
				if (doc != null && line <= doc.getNumberOfLines()) {
					IRegion reg = doc.getLineInformation(line - 1);
					te.selectAndReveal(reg.getOffset(), reg.getLength());
				}
			}
		} catch (Exception ignored) {
		}
	}

	private static final class LastSourceLineLink implements IHyperlink {
		private final int line;

		LastSourceLineLink(int line) {
			this.line = line;
		}

		@Override
		public void linkEntered() {
		}

		@Override
		public void linkExited() {
		}

		@Override
		public void linkActivated() {
			ShayaSourceResolver.ResolvedSource src = ShayaLastLaunch.lastSource();
			if (src == null) {
				return;
			}
			openAtLine(src.workspaceFile, src.file, line);
		}
	}

	private static final class FileLineLink implements IHyperlink {
		private final String path;
		private final int line;

		FileLineLink(String path, int line) {
			this.path = path;
			this.line = line;
		}

		@Override
		public void linkEntered() {
		}

		@Override
		public void linkExited() {
		}

		@Override
		public void linkActivated() {
			ResolvedLink resolved = resolve(path);
			openAtLine(resolved.workspaceFile, resolved.diskFile, line);
		}

		private static final class ResolvedLink {
			final IFile workspaceFile;
			final File diskFile;

			ResolvedLink(IFile workspaceFile, File diskFile) {
				this.workspaceFile = workspaceFile;
				this.diskFile = diskFile;
			}
		}

		private static ResolvedLink resolve(String raw) {
			String p = raw.replace('/', '\\');
			IPath ipath = Path.fromOSString(p);
			if (ipath.isAbsolute()) {
				File disk = ipath.toFile();
				IFile[] files = ResourcesPlugin.getWorkspace().getRoot()
						.findFilesForLocationURI(disk.toURI());
				if (files != null) {
					for (IFile f : files) {
						if (f.exists()) {
							return new ResolvedLink(f, disk.isFile() ? disk : null);
						}
					}
				}
				if (disk.isFile()) {
					return new ResolvedLink(null, disk);
				}
			}

			final String name = ipath.lastSegment();
			if (name == null || name.isBlank()) {
				return new ResolvedLink(null, null);
			}

			// 1) Last launch / sibling of last source
			ShayaSourceResolver.ResolvedSource last = ShayaLastLaunch.lastSource();
			if (last != null && last.file != null) {
				if (name.equalsIgnoreCase(last.file.getName())) {
					return new ResolvedLink(last.workspaceFile, last.file);
				}
				File sibling = new File(last.file.getParentFile(), name);
				if (sibling.isFile()) {
					IFile ws = findExactWorkspace(sibling);
					return new ResolvedLink(ws, sibling);
				}
			}

			final List<IFile> found = new ArrayList<>();
			try {
				ResourcesPlugin.getWorkspace().getRoot().accept(new IResourceProxyVisitor() {
					@Override
					public boolean visit(IResourceProxy proxy) {
						if (proxy.getType() == IResource.FILE && name.equalsIgnoreCase(proxy.getName())) {
							IResource r = proxy.requestResource();
							if (r instanceof IFile) {
								found.add((IFile) r);
							}
						}
						return true;
					}
				}, IResource.NONE);
			} catch (CoreException ignored) {
			}

			if (found.isEmpty()) {
				File loose = new File(name);
				return new ResolvedLink(null, loose.isFile() ? loose : null);
			}
			if (found.size() == 1) {
				return new ResolvedLink(found.get(0), null);
			}

			// 2) Prefer same project as last launch
			if (last != null && last.workspaceFile != null) {
				String proj = last.workspaceFile.getProject().getName();
				List<IFile> sameProj = new ArrayList<>();
				for (IFile f : found) {
					if (proj.equals(f.getProject().getName())) {
						sameProj.add(f);
					}
				}
				if (sameProj.size() == 1) {
					return new ResolvedLink(sameProj.get(0), null);
				}
				if (sameProj.size() > 1) {
					return chooseAmong(sameProj, name);
				}
			}

			// 3) Ambiguous — ask
			return chooseAmong(found, name);
		}

		private static IFile findExactWorkspace(File disk) {
			try {
				IFile[] files = ResourcesPlugin.getWorkspace().getRoot()
						.findFilesForLocationURI(disk.getCanonicalFile().toURI());
				if (files != null) {
					for (IFile f : files) {
						if (f.exists()) {
							return f;
						}
					}
				}
			} catch (Exception ignored) {
			}
			return null;
		}

		private static ResolvedLink chooseAmong(List<IFile> candidates, String name) {
			IFile[] arr = candidates.toArray(new IFile[0]);
			final IFile[] chosen = new IFile[1];
			Display display = Display.getDefault();
			Runnable pick = () -> {
				Shell shell = PlatformUI.getWorkbench().getActiveWorkbenchWindow() != null
						? PlatformUI.getWorkbench().getActiveWorkbenchWindow().getShell()
						: null;
				ElementListSelectionDialog dlg = new ElementListSelectionDialog(shell, new LabelProvider() {
					@Override
					public String getText(Object element) {
						if (element instanceof IFile) {
							return ((IFile) element).getFullPath().toString();
						}
						return super.getText(element);
					}
				});
				dlg.setTitle("ALG — several files named " + name);
				dlg.setMessage("Pick the source for this console link:");
				dlg.setElements(arr);
				if (dlg.open() == Window.OK && dlg.getFirstResult() instanceof IFile) {
					chosen[0] = (IFile) dlg.getFirstResult();
				}
			};
			if (display.getThread() == Thread.currentThread()) {
				pick.run();
			} else {
				display.syncExec(pick);
			}
			return new ResolvedLink(chosen[0] != null ? chosen[0] : candidates.get(0), null);
		}
	}
}
