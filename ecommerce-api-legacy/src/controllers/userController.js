const userModel = require('../models/userModel');

function deleteUser(req, res, next) {
    try {
        const id = req.params.id;
        userModel.deleteById(id);
        return res.json({ msg: 'Usuário deletado' });
    } catch (err) {
        next(err);
    }
}

module.exports = { deleteUser };
