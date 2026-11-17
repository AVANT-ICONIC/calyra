//! CALYRA source-pinned experiment: one authoritative non-text native input[type=range] state.
//!
//! Lives only in a disposable upstream Blitz checkout. No Parley PlainEditor,
//! no parallel Boa state, no synthetic user input/change events. This restricted
//! model covers numeric finite endpoints, clamp/step and live current/default
//! separation. Attribute mutation and full HTML range algorithms remain scoped.
use markup5ever::local_name;
use crate::ElementData;

#[derive(Clone, Debug, PartialEq)]
pub struct RangeData {
    pub minimum: f64,
    pub maximum: f64,
    pub step: Option<f64>,
    pub default_value: f64,
    pub value: f64,
}

impl RangeData {
    pub fn from_element(el: &ElementData) -> Self {
        let minimum = el.attr_parsed::<f64>(local_name!("min"))
            .filter(|v| v.is_finite()).unwrap_or(0.0);
        let maximum = el.attr_parsed::<f64>(local_name!("max"))
            .filter(|v| v.is_finite() && *v >= minimum)
            .unwrap_or(100.0_f64.max(minimum));
        let step = match el.attr(local_name!("step")) {
            Some("any") => None,
            Some(raw) => Some(raw.parse::<f64>().ok()
                .filter(|v| v.is_finite() && *v > 0.0).unwrap_or(1.0)),
            None => Some(1.0),
        };
        let mut data = Self {
            minimum, maximum, step,
            default_value: 0.0, value: 0.0,
        };
        let default_raw = el.attr(local_name!("value")).unwrap_or("");
        data.default_value = data.normalize_raw(default_raw);
        data.value = data.default_value;
        data
    }

    pub fn normalize_raw(&self, raw: &str) -> f64 {
        let fallback = self.minimum + (self.maximum - self.minimum) / 2.0;
        let parsed = raw.trim().parse::<f64>().ok()
            .filter(|v| v.is_finite()).unwrap_or(fallback);
        self.normalize_number(parsed)
    }

    pub fn normalize_number(&self, value: f64) -> f64 {
        let mut value = if value.is_finite() {
            value.clamp(self.minimum, self.maximum)
        } else {
            self.minimum + (self.maximum - self.minimum) / 2.0
        };
        if let Some(step) = self.step {
            // Restrict snapping to safe finite intermediate values to avoid NaN
            // and overflow for huge but technically finite attributes.
            let steps = (value - self.minimum) / step;
            if steps.is_finite() {
                let snapped = self.minimum + steps.round() * step;
                if snapped.is_finite() {
                    value = snapped.clamp(self.minimum, self.maximum);
                }
            }
        }
        value
    }

    /// The DOM current value changes; defaultValue/HTML value attribute do not.
    /// Returns false for idempotent assignments.
    pub fn set_current(&mut self, raw: &str) -> bool {
        let next = self.normalize_raw(raw);
        if self.value == next { return false; }
        self.value = next;
        true
    }

    pub fn reset(&mut self) -> bool {
        if self.value == self.default_value { return false; }
        self.value = self.default_value;
        true
    }

    pub fn value_text(&self) -> String {
        self.value.to_string()
    }

    pub fn progress(&self) -> f64 {
        let span = self.maximum - self.minimum;
        if !(span > 0.0 && span.is_finite()) { return 0.0; }
        ((self.value - self.minimum) / span).clamp(0.0, 1.0)
    }
}
