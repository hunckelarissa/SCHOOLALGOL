package org.myau.shaya.ide.builder;

import java.util.Map;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceDelta;
import org.eclipse.core.resources.IResourceDeltaVisitor;
import org.eclipse.core.resources.IncrementalProjectBuilder;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.myau.shaya.ide.run.ShayaLauncher;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Incremental builder: --check on changed ALG sources where the engine supports it.
 */
public class ShayaBuilder extends IncrementalProjectBuilder {

	public static final String BUILDER_ID = "org.myau.shaya.ide.shayaBuilder";

	@Override
	protected IProject[] build(int kind, Map<String, String> args, IProgressMonitor monitor) throws CoreException {
		if (kind == FULL_BUILD) {
			fullBuild(monitor);
		} else {
			IResourceDelta delta = getDelta(getProject());
			if (delta == null) {
				fullBuild(monitor);
			} else {
				incrementalBuild(delta, monitor);
			}
		}
		return null;
	}

	private void fullBuild(IProgressMonitor monitor) throws CoreException {
		getProject().accept(resource -> {
			if (monitor.isCanceled()) {
				return false;
			}
			checkIfSupported(resource, monitor);
			return true;
		});
	}

	private void incrementalBuild(IResourceDelta delta, IProgressMonitor monitor) throws CoreException {
		delta.accept((IResourceDeltaVisitor) d -> {
			if (monitor.isCanceled()) {
				return false;
			}
			IResource resource = d.getResource();
			if (d.getKind() != IResourceDelta.REMOVED) {
				checkIfSupported(resource, monitor);
			}
			return true;
		});
	}

	private static void checkIfSupported(IResource resource, IProgressMonitor monitor) {
		if (!(resource instanceof IFile)) {
			return;
		}
		IFile file = (IFile) resource;
		String engine = ShayaToolchain.engineIdForName(file.getName());
		if (engine == null || !ShayaToolchain.supportsCheck(engine)) {
			return;
		}
		ShayaLauncher.checkSync(file, monitor);
	}
}
