package org.myau.shaya.ide.nature;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IProjectDescription;
import org.eclipse.core.runtime.CoreException;

/** Add / remove ALG nature (builder via ShayaNature.configure). */
public final class ShayaNatureSupport {

	private ShayaNatureSupport() {
	}

	public static boolean hasNature(IProject project) throws CoreException {
		return project.isAccessible() && project.hasNature(ShayaNature.NATURE_ID);
	}

	public static void addNature(IProject project) throws CoreException {
		if (!project.isAccessible() || hasNature(project)) {
			return;
		}
		IProjectDescription description = project.getDescription();
		List<String> natures = new ArrayList<>(Arrays.asList(description.getNatureIds()));
		natures.add(ShayaNature.NATURE_ID);
		description.setNatureIds(natures.toArray(new String[0]));
		project.setDescription(description, null);
	}

	public static void removeNature(IProject project) throws CoreException {
		if (!project.isAccessible() || !hasNature(project)) {
			return;
		}
		IProjectDescription description = project.getDescription();
		List<String> natures = new ArrayList<>(Arrays.asList(description.getNatureIds()));
		natures.remove(ShayaNature.NATURE_ID);
		description.setNatureIds(natures.toArray(new String[0]));
		project.setDescription(description, null);
	}

	public static void toggleNature(IProject project) throws CoreException {
		if (hasNature(project)) {
			removeNature(project);
		} else {
			addNature(project);
		}
	}
}
