"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _N3Store = _interopRequireDefault(require("./N3Store"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { default: e }; }
class N3DatasetCoreFactory {
  dataset(quads) {
    return new _N3Store.default(quads);
  }
}
exports.default = N3DatasetCoreFactory;