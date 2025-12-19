type DeleteHandler = (id: string) => Promise<void>;

let deleteHandler: DeleteHandler = async () => {};

export const setDeleteConversationHandler = (handler: DeleteHandler) => {
  deleteHandler = handler;
};

export const deleteConversationById = async (id: string) => deleteHandler(id);
