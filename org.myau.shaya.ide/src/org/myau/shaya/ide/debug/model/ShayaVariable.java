package org.myau.shaya.ide.debug.model;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.model.IValue;
import org.eclipse.debug.core.model.IVariable;
import org.myau.shaya.ide.debug.ShayaDebugEvent;
import org.myau.shaya.ide.debug.ShayaJson;

/**
 * Переменная ALG (globals/locals/arrays/records при паузе).
 */
public class ShayaVariable extends ShayaDebugElement implements IVariable {

	private final String name;
	private final ShayaValue value;
	private final boolean changed;

	public ShayaVariable(ShayaDebugTarget target, String name, String valueText) {
		this(target, name, valueText, false);
	}

	public ShayaVariable(ShayaDebugTarget target, String name, String valueText, boolean changed) {
		this(target, name, new ShayaValue(target, valueText), changed);
	}

	public ShayaVariable(ShayaDebugTarget target, String name, ShayaValue value, boolean changed) {
		super(target, target.getLaunch());
		this.name = name;
		this.value = value;
		this.changed = changed;
	}

	/** Строит переменную из JSON-значения протокола (скаляр / массив / запись). */
	public static ShayaVariable fromProtocol(ShayaDebugTarget target, String name, Object raw,
			boolean changed) {
		return new ShayaVariable(target, name, valueFromProtocol(target, raw), changed);
	}

	static ShayaValue valueFromProtocol(ShayaDebugTarget target, Object raw) {
		if (raw instanceof Map) {
			@SuppressWarnings("unchecked")
			Map<String, Object> m = (Map<String, Object>) raw;
			String kind = m.get("kind") == null ? "" : String.valueOf(m.get("kind"));
			if ("array".equals(kind)) {
				Map<String, Object> values = ShayaJson.asObject(m.get("values"));
				List<IVariable> kids = new ArrayList<>();
				for (Map.Entry<String, Object> e : values.entrySet()) {
					kids.add(fromProtocol(target, "[" + e.getKey() + "]", e.getValue(), false));
				}
				return new ShayaValue(target, ShayaDebugEvent.stringify(raw),
						kids.toArray(new IVariable[0]));
			}
			if ("record".equals(kind)) {
				Map<String, Object> fields = ShayaJson.asObject(m.get("fields"));
				List<IVariable> kids = new ArrayList<>();
				for (Map.Entry<String, Object> e : fields.entrySet()) {
					kids.add(fromProtocol(target, e.getKey(), e.getValue(), false));
				}
				return new ShayaValue(target, ShayaDebugEvent.stringify(raw),
						kids.toArray(new IVariable[0]));
			}
			// обычный dict — дети по ключам
			List<IVariable> kids = new ArrayList<>();
			for (Map.Entry<String, Object> e : m.entrySet()) {
				kids.add(fromProtocol(target, e.getKey(), e.getValue(), false));
			}
			if (!kids.isEmpty()) {
				return new ShayaValue(target, ShayaDebugEvent.stringify(raw),
						kids.toArray(new IVariable[0]));
			}
		}
		if (raw instanceof List) {
			List<?> list = (List<?>) raw;
			List<IVariable> kids = new ArrayList<>();
			for (int i = 0; i < list.size(); i++) {
				kids.add(fromProtocol(target, "[" + i + "]", list.get(i), false));
			}
			return new ShayaValue(target, "list[" + list.size() + "]",
					kids.toArray(new IVariable[0]));
		}
		return new ShayaValue(target, ShayaDebugEvent.stringify(raw));
	}

	public String getValueText() {
		return value.getValueString();
	}

	void applySetResult(String newText) {
		value.updateText(newText);
	}

	/** Имя без префиксов local./arr./rec. для протокола set. */
	public String bareName() {
		if (name.startsWith("local.")) {
			return name.substring(6);
		}
		if (name.startsWith("arr.") || name.startsWith("rec.")) {
			return name;
		}
		return name;
	}

	public boolean isSettable() {
		return !name.startsWith("arr.") && !name.startsWith("rec.") && !name.contains("[");
	}

	@Override
	public void setValue(String expression) throws DebugException {
		if (!isSettable()) {
			notSupported("setValue(массив/запись)");
		}
		ShayaDebugTarget target = (ShayaDebugTarget) getDebugTarget();
		target.setVariable(bareName(), expression == null ? "" : expression.trim());
	}

	@Override
	public void setValue(IValue value) throws DebugException {
		if (value == null) {
			notSupported("setValue");
		}
		setValue(value.getValueString());
	}

	@Override
	public boolean supportsValueModification() {
		return isSettable();
	}

	@Override
	public boolean verifyValue(String expression) {
		return expression != null && !expression.isBlank() && isSettable();
	}

	@Override
	public boolean verifyValue(IValue value) {
		try {
			return value != null && verifyValue(value.getValueString());
		} catch (DebugException e) {
			return false;
		}
	}

	@Override
	public IValue getValue() {
		return value;
	}

	@Override
	public String getName() {
		return name;
	}

	@Override
	public String getReferenceTypeName() {
		return "ALG";
	}

	@Override
	public boolean hasValueChanged() {
		return changed;
	}
}
