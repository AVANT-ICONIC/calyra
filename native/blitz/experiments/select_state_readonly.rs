//! CALYRA Stage A only: minimal single-select current-state experiment.
//!
//! This module lives exclusively in a temporary pinned Blitz checkout. It
//! models current option selection separately from HTML's defaultSelected
//! attribute. It deliberately handles only *direct* option children,
//! without optgroups, disabled handling, popups or user-event synthesis.
//! The selected option and its read-only Parley layout live on the native
//! SelectData of the DOM node. No PlainEditor or duplicated Boa state.
use crate::dom::{dom_ctx, js_str, this_node_id, to_rust_string};
use crate::state::DomCtx;
use blitz_dom::{NodeId, local_name};
use boa_engine::{Context, JsResult, JsValue};

pub(super) fn is_select(ctx: &DomCtx, node_id: NodeId) -> bool {
    ctx.doc.borrow().get_node(node_id)
        .is_some_and(|node| node.data.is_element_with_tag_name(&local_name!("select")))
}

fn is_option(ctx: &DomCtx, node_id: NodeId) -> bool {
    ctx.doc.borrow().get_node(node_id)
        .is_some_and(|node| node.data.is_element_with_tag_name(&local_name!("option")))
}

fn parent_select(ctx: &DomCtx, option_id: NodeId) -> Option<NodeId> {
    let doc = ctx.doc.borrow();
    let parent_id = doc.get_node(option_id)?.parent?;
    doc.get_node(parent_id)?.data.is_element_with_tag_name(&local_name!("select"))
        .then_some(parent_id)
}

fn options(ctx: &DomCtx, select: NodeId) -> Vec<NodeId> {
    let doc = ctx.doc.borrow();
    doc.get_node(select).map(|node| {
        node.children.iter().copied().filter(|id| {
            doc.get_node(*id).is_some_and(|child|
                child.data.is_element_with_tag_name(&local_name!("option")))
        }).collect()
    }).unwrap_or_default()
}

fn option_value(ctx: &DomCtx, option_id: NodeId) -> String {
    let doc = ctx.doc.borrow();
    doc.get_node(option_id).map(|node| {
        node.attr(local_name!("value")).map(str::to_owned)
            .unwrap_or_else(|| node.text_content().trim().to_string())
    }).unwrap_or_default()
}

fn current(ctx: &DomCtx, select: NodeId) -> Option<NodeId> {
    // The DOM select owns its current selection. No parallel Boa state map.
    let doc = ctx.doc.borrow();
    doc.get_node(select)
        .and_then(|node| node.element_data())
        .and_then(|element| element.select_data())
        .and_then(|data| data.selected_option)
}

fn update(ctx: &DomCtx, select: NodeId, chosen: Option<NodeId>) {
    ctx.doc.borrow_mut().calyra_set_select_selection(select, chosen);
}

pub(super) fn get_value(this: &JsValue, _args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    let selected = current(&ctx, id);
    Ok(js_str(&selected.map(|option| option_value(&ctx, option)).unwrap_or_default()))
}

pub(super) fn set_value(this: &JsValue, args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let value = to_rust_string(args.first().unwrap_or(&JsValue::undefined()), context)?;
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    let chosen = options(&ctx, id).into_iter()
        .find(|option| option_value(&ctx, *option) == value);
    update(&ctx, id, chosen);
    Ok(JsValue::undefined())
}

pub(super) fn get_selected_index(this: &JsValue, _args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    if !is_select(&ctx,id) { return Ok(JsValue::undefined()); }
    let selected = current(&ctx,id);
    let index = options(&ctx,id).iter().position(|option| Some(*option) == selected)
        .map(|n| n as i32).unwrap_or(-1);
    Ok(JsValue::from(index))
}

pub(super) fn set_selected_index(this: &JsValue, args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let number = args.first().unwrap_or(&JsValue::undefined()).to_number(context)?;
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    if !is_select(&ctx,id) { return Ok(JsValue::undefined()); }
    let chosen = if number >= 0.0 && number < i32::MAX as f64 {
        options(&ctx,id).get(number as usize).copied()
    } else { None };
    update(&ctx,id,chosen);
    Ok(JsValue::undefined())
}

pub(super) fn get_selected(this: &JsValue, _args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    if !is_option(&ctx,id) { return Ok(JsValue::undefined()); }
    let selected = parent_select(&ctx,id).is_some_and(|select| current(&ctx,select) == Some(id));
    Ok(JsValue::from(selected))
}

pub(super) fn set_selected(this: &JsValue, args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let chosen = args.first().is_some_and(JsValue::to_boolean);
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    if let Some(select) = parent_select(&ctx,id) {
        if chosen { update(&ctx,select,Some(id)); }
        else if current(&ctx,select) == Some(id) { update(&ctx,select,None); }
    }
    Ok(JsValue::undefined())
}

pub(super) fn get_default_selected(this: &JsValue, _args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    if !is_option(&ctx,id) { return Ok(JsValue::undefined()); }
    let attr = ctx.doc.borrow().get_node(id)
        .is_some_and(|node| node.attr(local_name!("selected")).is_some());
    Ok(JsValue::from(attr))
}

pub(super) fn set_default_selected(this: &JsValue, args: &[JsValue], context: &mut Context) -> JsResult<JsValue> {
    let checked = args.first().is_some_and(JsValue::to_boolean);
    let ctx = dom_ctx(context)?;
    let id = this_node_id(this)?;
    if !is_option(&ctx,id) { return Ok(JsValue::undefined()); }
    let mut doc = ctx.doc.borrow_mut();
    if checked { doc.mutate().set_attribute(id, super::attributes::attr_name("selected"), ""); }
    else { doc.mutate().clear_attribute(id, super::attributes::attr_name("selected")); }
    // Attribute mutation does not change an already-initialized live selection.
    Ok(JsValue::undefined())
}
