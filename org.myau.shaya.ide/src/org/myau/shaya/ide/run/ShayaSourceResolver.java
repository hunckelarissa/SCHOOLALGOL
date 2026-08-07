package org.myau.shaya.ide.run;

import java.io.File;
import java.net.URI;

import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.filesystem.EFS;
import org.eclipse.core.filesystem.IFileStore;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IPath;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IFileEditorInput;
import org.eclipse.ui.IPathEditorInput;
import org.eclipse.ui.IURIEditorInput;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.ide.FileStoreEditorInput;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Resolves the ALG source file to act on: active editor first, then selection.
 * Mirrors the Myau MyauBuildHandler.resolveSource pattern.
 */
public final class ShayaSourceResolver {

	private ShayaSourceResolver() {
	}

	public static ResolvedSource resolveFromEditor(IEditorPart editor) {
		if (editor == null) {
			return null;
		}
		return fromEditorInput(editor.getEditorInput());
	}

	public static ResolvedSource resolveSource(ExecutionEvent event) {
		IEditorPart editor = HandlerUtil.getActiveEditor(event);
		ResolvedSource fromEditor = resolveFromEditor(editor);
		if (fromEditor != null) {
			return fromEditor;
		}
		ISelection sel = HandlerUtil.getCurrentSelection(event);
		if (sel instanceof IStructuredSelection) {
			Object el = ((IStructuredSelection) sel).getFirstElement();
			if (el instanceof IFile) {
				IFile f = (IFile) el;
				if (ShayaToolchain.isShayaSource(f.getName())) {
					File loc = f.getLocation() != null ? f.getLocation().toFile() : null;
					if (loc != null) {
						return new ResolvedSource(loc, f);
					}
				}
			}
		}
		return null;
	}

	private static ResolvedSource fromEditorInput(IEditorInput input) {
		if (input == null) {
			return null;
		}
		if (input instanceof IFileEditorInput) {
			IFile f = ((IFileEditorInput) input).getFile();
			if (ShayaToolchain.isShayaSource(f.getName())) {
				IPath loc = f.getLocation();
				if (loc != null) {
					return new ResolvedSource(loc.toFile(), f);
				}
			}
			return null;
		}
		File disk = null;
		if (input instanceof IURIEditorInput) {
			URI uri = ((IURIEditorInput) input).getURI();
			if (uri != null && "file".equalsIgnoreCase(uri.getScheme())) {
				disk = new File(uri);
			}
		}
		if (disk == null && input instanceof IPathEditorInput) {
			IPath path = ((IPathEditorInput) input).getPath();
			if (path != null) {
				disk = path.toFile();
			}
		}
		if (disk == null && input instanceof FileStoreEditorInput) {
			try {
				IFileStore store = EFS.getStore(((FileStoreEditorInput) input).getURI());
				disk = store.toLocalFile(EFS.NONE, null);
			} catch (CoreException ignored) {
			}
		}
		if (disk == null || !disk.isFile() || !ShayaToolchain.isShayaSource(disk.getName())) {
			return null;
		}
		IFile ws = findWorkspaceFile(disk);
		return new ResolvedSource(disk, ws);
	}

	private static IFile findWorkspaceFile(File disk) {
		try {
			URI uri = disk.getCanonicalFile().toURI();
			IWorkspaceRoot root = ResourcesPlugin.getWorkspace().getRoot();
			IFile[] files = root.findFilesForLocationURI(uri);
			if (files != null && files.length > 0) {
				return files[0];
			}
		} catch (Exception ignored) {
		}
		return null;
	}

	/** Disk path always; workspace IFile when the resource exists in a project. */
	public static final class ResolvedSource {
		public final File file;
		public final IFile workspaceFile;

		public ResolvedSource(File file, IFile workspaceFile) {
			this.file = file;
			this.workspaceFile = workspaceFile;
		}
	}
}
