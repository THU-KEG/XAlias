from src.model.GLM.generate_samples import init_glm, call_glm_generate

model, tokenizer, args, device = init_glm()
# input_text = "Blink ( ability ) is also called blink. Callahuanca ( short story ) is also called callahuanca. Mole rat wonder meat ( Fallout 3 ) is also called mole rat wonder meat. Cold War ( TV story ) is also called [MASK]."
input_text = "ussr is the short for union of soviet socialist republics. [MASK] is the short for united states of america."
result = call_glm_generate(model, tokenizer, args, device, input_text)
print("Final glm returns:")
print(result)
