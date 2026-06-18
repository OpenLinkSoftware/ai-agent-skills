"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.escapeRegex = escapeRegex;
function escapeRegex(regex) {
  return regex.replace(/[\]\/\(\)\*\+\?\.\\\$]/g, '\\$&');
}