package org.myau.shaya.ide.debug;

import java.io.File;

import org.eclipse.core.filesystem.EFS;
import org.eclipse.core.filesystem.IFileStore;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.IPath;
import org.eclipse.core.runtime.Path;
import org.eclipse.jface.text.IDocument;
import org.eclipse.swt.widgets.Display;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.texteditor.ITextEditor;

/**
 * Открытие исходника по path/line (стек / текущая позиция).
 * Если path указывает на файл вне workspace — открывает через EFS FileStore.
 */
public final class ShayaSourceReveal {

	private ShayaSourceReveal() {
	}

	public static void reveal(IFile fallback, String path, int line1Based) {
		if (line1Based < 1) {
			return;
		}
		Display.getDefault().asyncExec(() -> {
			try {
				if (!PlatformUI.isWorkbenchRunning()) {
					return;
				}
				IWorkbenchPage page = PlatformUI.getWorkbench().getActiveWorkbenchWindow() != null
						? PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage()
						: null;
				if (page == null) {
					return;
				}
				IFile file = resolve(fallback, path);
				IEditorPart editor = null;
				if (file != null && file.exists()) {
					editor = IDE.openEditor(page, file, true);
				} else if (path != null && !path.isBlank()) {
					File disk = Path.fromOSString(path.trim()).toFile();
					if (disk.isFile()) {
						IFileStore store = EFS.getLocalFileSystem().getStore(new Path(disk.getAbsolutePath()));
						editor = IDE.openEditorOnFileStore(page, store);
					}
				}
				if (editor == null && fallback != null && fallback.exists()) {
					editor = IDE.openEditor(page, fallback, true);
				}
				if (!(editor instanceof ITextEditor)) {
					return;
				}
				ITextEditor textEditor = (ITextEditor) editor;
				IDocument doc = textEditor.getDocumentProvider().getDocument(editor.getEditorInput());
				if (doc != null && line1Based <= doc.getNumberOfLines()) {
					int offset = doc.getLineOffset(line1Based - 1);
					int length = doc.getLineLength(line1Based - 1);
					textEditor.selectAndReveal(offset, Math.max(0, length - 1));
				}
			} catch (Exception ignored) {
			}
		});
	}

	public static IFile resolve(IFile fallback, String path) {
		if (path != null && !path.isBlank()) {
			try {
				File disk = Path.fromOSString(path.trim()).toFile();
				if (disk.isFile()) {
					try {
						disk = disk.getCanonicalFile();
					} catch (Exception ignored) {
					}
					IWorkspaceRoot root = ResourcesPlugin.getWorkspace().getRoot();
					IFile[] found = root.findFilesForLocation(Path.fromOSString(disk.getAbsolutePath()));
					if (found != null && found.length > 0 && found[0].exists()) {
						return found[0];
					}
					IFile[] again = root.findFilesForLocationURI(disk.toURI());
					if (again != null && again.length > 0 && again[0].exists()) {
						return again[0];
					}
				} else {
					IPath abs = Path.fromOSString(path.trim());
					IWorkspaceRoot root = ResourcesPlugin.getWorkspace().getRoot();
					IFile[] found = root.findFilesForLocation(abs);
					if (found != null && found.length > 0 && found[0].exists()) {
						return found[0];
					}
				}
			} catch (Exception ignored) {
			}
			// path set but not in workspace — caller may open via FileStore
			return null;
		}
		return fallback;
	}
}